-- Part D business questions on Google BigQuery (dataset idp, region asia-south1).
-- Same answers as sql/03_business_queries.sql on PostgreSQL; run with:  bq query --use_legacy_sql=false < file

-- Q1  Fleet KPIs: machine-hours, parts, reject rate, OEE (same formula as the dashboard)
SELECT
  COUNT(*)                                                     AS machine_hours,
  SUM(production_count)                                        AS parts,
  ROUND(100 * SUM(reject_count) / SUM(production_count), 2)    AS reject_pct,
  ROUND(100 * SAFE_DIVIDE(SUM(running_minutes), 60 * COUNTIF(machine_status != 'OFF'))
            * LEAST(SAFE_DIVIDE(SUM(production_count), SUM(ideal_count)), 1)
            * (1 - SAFE_DIVIDE(SUM(reject_count), SUM(production_count))), 1) AS oee_pct
FROM idp.machine_data;

-- Q2  Top 5 machines by parts produced
SELECT m.machine_code, SUM(d.production_count) AS parts
FROM idp.machine_data d JOIN idp.machine_master m USING (machine_id)
GROUP BY m.machine_code ORDER BY parts DESC LIMIT 5;

-- Q3  Highest reject rate per machine
SELECT m.machine_code, ROUND(100 * SUM(d.reject_count) / SUM(d.production_count), 2) AS reject_pct
FROM idp.machine_data d JOIN idp.machine_master m USING (machine_id)
GROUP BY m.machine_code ORDER BY reject_pct DESC LIMIT 5;

-- Q4  Plant comparison: parts, alarms, average temperature and vibration
SELECT p.plant_code, p.location, SUM(d.production_count) AS parts, SUM(d.alarm_count) AS alarms,
       ROUND(AVG(d.temperature), 1) AS avg_temp_c, ROUND(AVG(d.vibration), 2) AS avg_vib_mm_s
FROM idp.machine_data d JOIN idp.plant p USING (plant_id)
GROUP BY p.plant_code, p.location ORDER BY p.plant_code;

-- Q5  Bosch edge features: bad operations vibrate harder (real data)
SELECT label, COUNT(*) AS seconds, ROUND(AVG(x_rms), 3) AS avg_x_rms
FROM idp.bosch_features_1s GROUP BY label;
