"""Data access for the dashboard.

Backend selection (automatic):
  * PostgreSQL when credentials are found (st.secrets["postgres"] or dashboard/.streamlit/secrets.toml)
    and the server answers - the local mode.
  * Else Google BigQuery when st.secrets has [bigquery] (+ [gcp_service_account] on the hosted app)
    and the dataset answers - the cloud-warehouse mode.
  * Otherwise the bundled Parquet snapshot in data/processed/ - the hosted mode (Streamlit
    Community Cloud), which cannot break on demo day.
All backends return identical DataFrames, so every page runs the same analysis code.
IDP_BACKEND=parquet|bigquery|postgres forces one (IDP_FORCE_PARQUET=1 still works).
"""
from __future__ import annotations

import io
import json
import os
import tomllib
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
REFERENCE = ROOT / "data" / "reference"
SAMPLES = ROOT / "data" / "samples"
RESULTS = ROOT / "docs" / "results"
SQL_RESULTS = ROOT / "sql" / "results"
FIGURES = ROOT / "docs" / "figures"

FACT_COLS = ["machine_id", "ts", "plant_id", "part_family_id", "shift", "temperature", "vibration", "rpm", "current",
             "production_count", "reject_count", "machine_status", "alarm", "alarm_code", "alarm_count",
             "tool_wear_min", "running_minutes", "spindle_load_pct", "power_kw", "ideal_count"]
STATUS_ORDER = ["RUNNING", "IDLE", "ALARM", "MAINTENANCE", "OFF"]


def _pg_params() -> dict | None:
    try:
        return dict(st.secrets["postgres"])
    except Exception:
        f = ROOT / "dashboard" / ".streamlit" / "secrets.toml"
        if f.exists():
            return tomllib.loads(f.read_text()).get("postgres")
    return None


def _bq_params() -> dict | None:
    try:
        return dict(st.secrets["bigquery"])            # {"project": ..., "dataset": ...}
    except Exception:
        if os.environ.get("IDP_BACKEND") == "bigquery":  # local test with `gcloud auth application-default login`
            return {"project": os.environ.get("IDP_BQ_PROJECT", "project-cc51f331-7539-4662-a83"), "dataset": "idp"}
    return None


@st.cache_resource(show_spinner=False)
def _bq_client():
    from google.cloud import bigquery
    p = _bq_params()
    try:
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]))
    except Exception:
        creds = None                                   # falls back to application-default credentials
    return bigquery.Client(project=p["project"], credentials=creds)


def _bq_frame(sql: str) -> pd.DataFrame:
    return _bq_client().query(sql).to_dataframe()


def _bq_table(name: str) -> str:
    p = _bq_params()
    return f"`{p['project']}.{p['dataset']}.{name}`"


def _pg_ok() -> bool:
    p = _pg_params()
    if not p:
        return False
    try:
        import psycopg
        with psycopg.connect(connect_timeout=3, **p) as c:
            c.execute("SELECT 1 FROM core.machine_data LIMIT 1")
        return True
    except Exception:
        return False


def _bq_ok() -> bool:
    if not _bq_params():
        return False
    try:
        _bq_frame(f"SELECT 1 FROM {_bq_table('machine_data')} LIMIT 1")
        return True
    except Exception:
        return False


@st.cache_resource(show_spinner=False)
def backend() -> str:
    forced = "parquet" if os.environ.get("IDP_FORCE_PARQUET") == "1" else os.environ.get("IDP_BACKEND")
    if forced == "parquet":                            # simulates the hosted app without a warehouse
        return "parquet"
    if forced in (None, "postgres") and _pg_ok():
        return "postgres"
    if forced in (None, "bigquery") and _bq_ok():
        return "bigquery"
    return "parquet"


def _pg_frame(sql: str) -> pd.DataFrame:
    import psycopg
    buf = io.BytesIO()
    with psycopg.connect(**_pg_params(), options="-c TimeZone=Asia/Kolkata") as c, c.cursor() as cur:
        with cur.copy(f"COPY ({sql}) TO STDOUT WITH (FORMAT csv, HEADER)") as cp:
            for chunk in cp:
                buf.write(chunk)
    buf.seek(0)
    return pd.read_csv(buf)


# cache_resource keeps ONE shared copy of the 876k-row table. cache_data would hand every page run a
# fresh deserialised copy, which exhausted the hosted app's memory. Pages must treat it as read-only.
@st.cache_resource(show_spinner="Loading fleet data ...", ttl=3600)
def machine_data() -> pd.DataFrame:
    if backend() == "postgres":
        # epoch seconds parse ~100x faster than ISO strings with offsets
        cols = ", ".join("EXTRACT(EPOCH FROM ts)::bigint AS ts" if c == "ts" else c for c in FACT_COLS)
        df = _pg_frame(f"SELECT {cols} FROM core.machine_data")
        df["ts"] = pd.to_datetime(df["ts"], unit="s", utc=True).dt.tz_convert("Asia/Kolkata")
        df["alarm"] = df["alarm"].map({"t": True, "f": False, True: True, False: False})
    elif backend() == "bigquery":
        df = _bq_frame(f"SELECT {', '.join(f'`{c}`' for c in FACT_COLS)} FROM {_bq_table('machine_data')}")  # `current` is reserved
        df["ts"] = pd.to_datetime(df["ts"], utc=True).dt.tz_convert("Asia/Kolkata")
        df["alarm"] = df["alarm"].astype(bool)
        for c in df.columns:                           # BigQuery returns 64-bit/nullable types; match the Parquet frame
            if str(df[c].dtype) in ("float64", "Float64"):
                df[c] = df[c].astype("float32")
            elif str(df[c].dtype) in ("int64", "Int64") and c != "ts":
                df[c] = df[c].astype("int16" if c == "alarm_count" else "int32")
            elif str(df[c].dtype) == "string":
                df[c] = df[c].astype(object)
    else:
        df = pd.read_parquet(PROCESSED / "machine_data.parquet", columns=FACT_COLS)
    df["machine_status"] = pd.Categorical(df["machine_status"], categories=STATUS_ORDER)
    for c in ("machine_id", "plant_id", "part_family_id"):
        df[c] = df[c].astype("int16")
    return df


@st.cache_data(show_spinner=False, ttl=3600)
def master() -> dict[str, pd.DataFrame]:
    if backend() == "postgres":
        m = {"machine": _pg_frame("SELECT * FROM core.machine"), "plant": _pg_frame("SELECT * FROM core.plant"),
             "part": _pg_frame("SELECT * FROM core.part_family"), "alarm": _pg_frame("SELECT * FROM core.alarm_master"),
             "type": _pg_frame("SELECT * FROM core.machine_type")}
    elif backend() == "bigquery":
        m = {k: _bq_frame(f"SELECT * FROM {_bq_table(t)}") for k, t in
             {"machine": "machine_master", "plant": "plant", "part": "part_master", "alarm": "alarm_master",
              "type": "machine_type"}.items()}
    else:
        m = {"machine": pd.read_csv(REFERENCE / "machine_master.csv"), "plant": pd.read_csv(REFERENCE / "plant.csv"),
             "part": pd.read_csv(REFERENCE / "part_master.csv"), "alarm": pd.read_csv(REFERENCE / "alarm_master.csv"),
             "type": pd.read_csv(REFERENCE / "machine_type.csv")}
    # identical columns from both backends: machine-type attributes always come from the type table
    t = m["type"][["machine_type", "rpm_min", "rpm_max", "rated_power_kw", "rated_current_a"]]
    m["machine"] = m["machine"].drop(columns=[c for c in t.columns if c != "machine_type"], errors="ignore") \
                               .merge(t, on="machine_type")
    m["machine"] = m["machine"].merge(m["plant"][["plant_id", "plant_code", "plant_name"]], on="plant_id") \
                               .merge(m["part"][["part_family_id", "part_name", "cycle_time_min"]], on="part_family_id")
    return m


@st.cache_data(show_spinner=False)
def events() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / "events.parquet")


@st.cache_data(show_spinner=False)
def risk_scores() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / "pdm_risk_scores.parquet")


@st.cache_data(show_spinner=False)
def bosch_sample() -> pd.DataFrame:
    return pd.read_parquet(SAMPLES / "bosch_sample_raw.parquet")


@st.cache_data(show_spinner=False)
def result_json(name: str) -> dict:
    return json.loads((RESULTS / f"{name}.json").read_text())


@st.cache_data(show_spinner=False)
def sql_result(name: str) -> pd.DataFrame:
    return pd.read_csv(SQL_RESULTS / f"{name}.csv")


def prices() -> dict:
    return json.loads((REFERENCE / "cloud_prices.json").read_text())
