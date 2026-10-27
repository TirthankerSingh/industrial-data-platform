# Presentation flow: slide by slide

**Story arc:** how factory data can flow → what we built and measured → how we compared and decided → **live demo**.

**Running time:** about 15–18 min plus Q&A. Each slide gives the **headline**, what goes **on the slide**, a **visual**, and what to **say**.

---

## Opening: the pipeline and the comparisons

### Slide 1: Title
- **Headline:** *From 31.5 billion readings to one decision: a smart-factory data platform*
- **On slide:**
  - 100 CNC machines · 3 plants (Chakan, Oragadam, Manesar) · real Bosch vibration data
  - Live dashboard URL · GitHub repo URL
- **Visual:** the plant-to-dashboard pipeline drawn as one thin line across the bottom.
- **Say:** *"We didn't just compare clouds on paper. We built the pipeline, measured it on real factory data, and the last slide is the live system."*

### Slide 2: The pipeline we built (the whole project on one slide)
- **Headline:** *Nine stages, one command to rebuild, one source of truth*
- **On slide:** Collect → Edge features → Calibrate → Fleet table → PostgreSQL / BigQuery → ML → MQTT gateway → Dashboard → Decision
- **Visual:** `diagrams/05_data_pipeline.png`
- **Say:**
  - *"Raw datasets go in on the left, a manufacturing decision comes out on the right."*
  - *"Every number in the report, slides and dashboard comes from these same scripts, so nothing is typed in by hand."*

### Slide 3: Pipeline comparison 1: how should data leave the machine?
- **Headline:** *The biggest cost decision isn't the cloud. It's the pipeline design.*
- **On slide:** a table of four ways to move the same data, with monthly cloud cost on Azure and AWS.

| Pipeline design | What travels | Azure / month | AWS / month |
|---|---|---|---|
| S0: one message per reading | 1,000 tiny messages a second | **₹14.3 lakh** | **₹29.9 lakh** |
| S3: raw 2 kHz vibration streamed | 96 Mbps, 378 TB a year | ₹3.9 lakh | ₹2.8 lakh |
| S1: batched raw 1 Hz + 100 Hz | Batched messages | ₹80k | ₹43k |
| **S2: batched + edge features** | **42 features a second instead of 6,000 samples** | **₹80k** | **₹43k** |

- **Visual:** `docs/figures/part_c_cost_model.png`
- **Say:** *"Same factory, same data, up to a 37× difference in the bill. Batching at the edge is the single biggest lever, bigger than which cloud you pick."*

### Slide 4: Pipeline comparison 2: compress or extract features?
- **Headline:** *Compression gives 5×. Feature extraction gives 143×.*
- **On slide:**
  - Raw Bosch vibration (2 kHz × 3 axes) compressed losslessly (Parquet + Zstd): **only 5×**, because vibration is mostly noise.
  - Edge features (RMS, kurtosis, crest factor, band energies), 42 per second: **143× smaller**.
  - Does the fault signal survive? **Yes: ROC-AUC 0.98** separating good from bad operations.
- **Visual:** `edge_waveform_vs_features.png` with `part_a_measured_compression.png` beside it.
- **Say:** *"This is measured on real Bosch production data, not assumed. You can't compress noise, but you can summarise it."*

### Slide 5: Storage comparison: lake vs warehouse vs lakehouse
- **Headline:** *Three shapes of data need three kinds of home*
- **On slide:**

| | Data lake | Data warehouse | **Lakehouse** |
|---|---|---|---|
| Holds | Everything, raw | Clean tables | Everything, plus clean tables |
| Structure | Decided when reading | Fixed before loading | Both |
| Cost | Lowest | Highest | Low |
| De-duplication, updates, history | No | Yes | **Yes** |
| Our data | Raw vibration (99 % of the bytes) | The fleet table, KPIs | **All of it, one copy** |

- **Visual:** three columns: storeroom, library, storeroom with a librarian.
- **Say:** *"Over 99 % of our bytes are raw vibration, the data that needs the least SQL. That one fact chooses the storage design."*

### Slide 6: Platform comparison: S3, Snowflake, Databricks, BigQuery, Fabric, PostgreSQL
- **Headline:** *Everyone is converging on the lakehouse*
- **On slide:**
  - **S3 / ADLS / GCS:** the lake, cheap and durable for raw signals.
  - **Snowflake / BigQuery / Redshift:** warehouses, the best SQL; awkward for raw signals.
  - **Databricks / Microsoft Fabric:** lakehouses, open Delta format, built for ML.
  - **PostgreSQL:** the application database, strict rules and fast lookups.
  - **Industry signal:** 65 % of enterprises already run most of their analytics on a lakehouse (Dremio 2024 survey, vendor-sponsored).
- **Say:** *"We used two of these for real: PostgreSQL locally and Google BigQuery in the cloud. You'll see BigQuery live in the demo."*

---

## Middle: what we did, part by part

### Slide 7: Our data, all real or benchmark and labelled honestly
- **Headline:** *Four public datasets, each with a job*
- **On slide:**
  - **Bosch CNC (REAL):** 1,702 operations at 2 kHz. Used for the edge proof and anomaly detection.
  - **UMich mill (REAL):** spindle current, tool wear and quality outcomes.
  - **Microsoft Azure PdM (BENCHMARK):** 100 machines × 1 year, which became our fleet backbone.
  - **AI4I 2020 (BENCHMARK):** machine physics and failure types.
  - Every calculated column is tagged **DERIVED**, with a provenance file.
- **Say:** *"Our rule was that no number appears without a source you can trace."*

### Slide 8: Part A: the data-volume problem
- **Headline:** *31.5 billion readings a year, before vibration*
- **On slide:**
  - **1 Hz fleet:** 1,000/s → 3.6 M/hour → 86.4 M/day → 2.59 B/month → **31.5 B/year**.
  - **One 100 Hz sensor:** 3.15 B/year per machine. On every machine that's **10× the entire fleet**.
  - **Real Bosch rate:** 96 Mbps and **378 TB a year** raw.
- **Visual:** `part_a_volume_per_year.png` (log scale)
- **Say:** *"One vibration sensor outweighs everything else combined. That's why the edge exists."*

### Slide 9: Part B: cloud comparison, the honest version
- **Headline:** *Half the 'IIoT services' in old comparisons no longer exist*
- **On slide:**
  - **Retired or in maintenance:** GCP IoT Core (2023), Azure Time Series Insights (2024), AWS IoT Analytics and IoT Events (2025–26).
  - **Azure:** the most complete current chain from OPC UA to dashboard (IoT Operations, Fabric, Power BI).
  - **AWS:** the best-documented edge buffering (Greengrass, SiteWise Edge).
  - **GCP:** the strongest, cheapest analytics (BigQuery), but no first-party factory-floor layer.
- **Say:** *"We checked every service against official vendor pages on 21 October. A comparison built from old blog posts would recommend dead products."*

### Slide 10: Part C: weighted decision matrix
- **Headline:** *Azure 4.22 · AWS 3.92 · GCP 3.57*
- **On slide:**
  - 10 criteria. The heaviest are Industrial IoT (15 %), cost (13 %), edge (12 %) and security (12 %).
  - Robustness: Azure wins **all ±5-point weight shifts** and **88.7 % of 10,000 random re-weightings**.
  - The flip point: AWS wins only if cost weight is at least 35 %.
- **Visual:** `part_c_weighted_scores.png` + `part_c_sensitivity.png`
- **Say:** *"The score isn't the argument. The scenario is: old OPC UA controllers, Microsoft tools already in the plants, and a Pune region next to Chakan."*

### Slide 11: Part F: architecture, recommended vs what we built
- **Headline:** *Every Azure block has a working stand-in in our prototype*

| Block | Azure (recommended) | Our prototype |
|---|---|---|
| Protocols | OPC UA + MQTT | MQTT with ISA-95 topics |
| Edge | IoT Operations, 7-day buffer | Python gateway with store-and-forward |
| Lake / time-series | ADLS lakehouse + Eventhouse | Parquet files, bronze/silver/gold |
| SQL | Azure Database for PostgreSQL | PostgreSQL 16 **+ Google BigQuery** |
| AI | Azure ML / Fabric | scikit-learn models |
| Dashboard | Power BI | **Streamlit, live** |

- **Visual:** `diagrams/02_reference_architecture.png`
- **Say:** *"Open formats everywhere. That's why we could move the same data to BigQuery in under an hour without changing a single query result."*

### Slide 12: Part G: edge vs cloud, proven with an outage test
- **Headline:** *We switched the internet off. 0 of 482 messages lost.*
- **On slide:**
  - **Edge:** 2 kHz processing, immediate alarms, machine protection, filtering, buffering.
  - **Cloud:** fleet history, ML training, long-term storage, dashboards.
  - **Why:** latency (milliseconds), reliability (outages), bandwidth (143×), cost (lakhs → thousands), security (outbound-only, IEC 62443 zones), scale (one edge node per plant).
- **Visual:** `edge_mqtt_store_and_forward.png`
- **Say:** *"We stopped the receiver, then cut the link. All 482 messages arrived exactly once."*

### Slide 13: Part D: SQL, one schema, two engines
- **Headline:** *876,100 machine-hours, same answers on PostgreSQL and BigQuery*
- **On slide:**
  - Most parts: **P3-TURN-05** with 199,677.
  - Worst reject rate: **P2-GRIND-06** at 1.97 %.
  - Longest run: **P1-HMC-18**, 209 h.
  - Highest vibration: **P1-VMC-13**, 1.86 mm/s (ISO zone B).
  - Fleet **OEE 75.3 %** against 85 % world-class.
- **Visual:** `diagrams/04_er_diagram.png` + a small results table.
- **Say:** *"Rules in the database reject impossible values. Running the same SQL on two engines and getting the same results is our proof of no lock-in."*

### Slide 14: Analytics and ML: climbing the ladder
- **Headline:** *Descriptive → diagnostic → predictive → prescriptive*
- **On slide:**
  - **Descriptive:** KPIs and OEE.
  - **Diagnostic:** alarm Pareto, ISO vibration zones.
  - **Predictive:** Bosch anomaly ROC-AUC **0.98** (holds from 2019 to 2021); 24-hour failure warning.
  - **Prescriptive:** tool changes on condition, rejects **1.50 % → 0.92 %**.
  - Estimated value: about **₹5.8 crore a year**.
- **Visual:** `ml_bosch_roc_pr_confusion.png`
- **Say:** *"We report precision too, because one industry study found a 10 % false-alarm rate wiped out the savings of predictive maintenance."*

### Slide 15: Why it matters, and what we're honest about
- **Headline:** *$2.3 M per hour of downtime in automotive, yet most factory data goes unused*
- **On slide:**
  - **Industry:** downtime costs the 500 largest industrial firms about 11 % of revenue (Siemens 2024); up to 80 % of industrial data is never used.
  - **Our limits:**
    - The fleet backbone is simulated (it is labelled as such).
    - The worn-tool model does not generalise across only 18 experiments.
    - The cloud deployment is a prototype on a BigQuery sandbox, not production Azure.
- **Say:** *"We'd rather show you where it breaks than hide it."*

---

## Close: live demo

### Slide 16: Demo, live system
- **Headline:** *Live: BigQuery (Mumbai) → read-only service account → Streamlit dashboard*
- **On slide:** the live URL, and a sidebar screenshot showing **Data source: Google BigQuery (asia-south1)**.

**Demo script (about 4–5 min):**
1. **Fleet overview:** point at the sidebar *"Data source: Google BigQuery"*. Read the KPIs: 83/100 running, OEE 75.5 %.
2. **Plant drill-down:** filter to one plant and show the plant heat map.
3. **Machine health:** vibration against the ISO 10816 zones.
4. **Alarms:** the Pareto chart, where the top 4 alarm types make up about 80 % of all alarms.
5. **Edge demo:** a real Bosch waveform next to its 42 features. *"This is the 143×."*
6. **Data volume & cost:** move the sliders and watch the monthly rupee cost jump when edge batching is switched off.
7. **Predictive maintenance:** the risk ranking of which machine to service first.
8. **Optional, 30 s:** the BigQuery console running the "most parts" query, which returns P3-TURN-05 = 199,677, the same as PostgreSQL.

**Before you present:**
- Open the app **10 minutes early**. The first load after the app sleeps takes about 20 s.
- **Backup:** keep screenshots of every page in a hidden slide, in case the venue Wi-Fi fails.

**Closing line:** *"Pipeline compared, platforms compared, decision made, and it's running. Thank you."*

---

### Backup slides (only if asked)
- **B1:** full 13-criterion cloud comparison table (report §4)
- **B2:** cost model assumptions in INR (FX ₹94.71 per USD, RBI, 21 Oct 2026)
- **B3:** security zones diagram (`diagrams/03_security_zones.png`)
