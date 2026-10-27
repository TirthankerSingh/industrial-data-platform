# Smart-Factory Cloud Data Platform: Technical Summary

<div class="meta">Tirthanker Singh · 28 October 2026 · Repository: https://github.com/TirthankerSingh/industrial-data-platform · Live dashboard: https://industrial-data-platform.streamlit.app · Full report: report.pdf</div>

**Scenario.** An automotive Tier-1 supplier runs **100 CNC machines in three plants**:
- **Chakan (Pune):** powertrain, 40 machines;
- **Oragadam (Chennai):** transmission, 35 machines;
- **Manesar (Gurugram):** chassis, 25 machines.

Each machine produces sensor, production and machine-control data, on Fanuc and Siemens controllers. The aim is to design and justify a cloud-data platform for monitoring, analytics, storage, dashboards, AI/ML and remote access.

**Evidence base.** Every number in this summary comes from **four public datasets** that were downloaded and processed:
- **Bosch CNC vibration** (REAL): 1,702 operations sampled at 2 kHz;
- **UMich CNC mill** (REAL);
- **Microsoft Azure Predictive Maintenance** (BENCHMARK): 100 machines × 1 year;
- **AI4I 2020** (BENCHMARK).

Values calculated from these are labelled DERIVED. The prototype includes a PostgreSQL database (876,100 machine-hours), the same data in Google BigQuery, an MQTT edge gateway, four machine-learning models and a live 8-page dashboard.

## A. Industrial data volume

| Stream | per second | per hour | per day | per month (30 d) | per year |
|---|---|---|---|---|---|
| Fleet: 100 machines × 10 sensors × 1 Hz | 1,000 | 3.6 M | 86.4 M | 2.59 B | **31.54 B** |
| One 100 Hz vibration sensor (one machine) | 100 | 360,000 | 8.64 M | 259.2 M | **3.15 B** |
| One 100 Hz sensor on every machine | 10,000 | 36 M | 864 M | 25.9 B | **315.4 B** |

- **The problem with high-frequency data.** A single 100 Hz sensor on every machine produces **10 times** the data of the entire 1 Hz fleet. At the real Bosch rate (2 kHz × 3 axes), raw vibration needs **96 Mbps and 378 TB a year**. That is too much for typical plant internet links and costly to store.
- **Compression alone doesn't solve it.** Lossless compression (Parquet + Zstd), measured on the real data, reached only **5×** on vibration, because vibration is mostly noise.
- **The answer is edge processing:**
  - **feature extraction:** 42 features per second (RMS, kurtosis, crest factor, frequency-band energy) give **143× less data**, and the fault signal survives (ROC-AUC **0.98** on real Bosch data);
  - **aggregation:** sensor readings are summarised to 1-minute and 1-hour values;
  - **noise filtering;**
  - **raw snippets only around anomalies.**
- **Result:** fleet bandwidth falls from **19.2 to 0.13 Mbps**.

## B. Cloud platform comparison

The comparison was checked against official vendor pages on 21 October 2026, including recent retirements: GCP IoT Core, Azure Time Series Insights, and AWS IoT Analytics and IoT Events.

| Criterion | AWS | Microsoft Azure | Google Cloud |
|---|---|---|---|
| Industrial IoT | SiteWise Edge reads OPC UA; several IIoT services retired | **IoT Operations: OPC UA connector, asset discovery** | No first-party IIoT; partner (Litmus) needed |
| Data ingestion | IoT Core, Kinesis | IoT Hub, Event Hubs, Eventstreams | Pub/Sub |
| Storage | S3, Timestream | ADLS Gen2, Eventhouse (time-series) | Cloud Storage, BigQuery, Bigtable |
| Stream processing | Kinesis, Flink (assembled from parts) | **Eventstreams with no-code windows and de-duplication** | Dataflow (code-first) |
| SQL / structured data | RDS / Aurora PostgreSQL | Azure Database for PostgreSQL | Cloud SQL, BigQuery |
| Analytics | Athena, QuickSight | KQL, Fabric, **Power BI** | **BigQuery (strongest SQL analytics)** |
| AI/ML | **SageMaker** | Azure ML, Fabric notebooks | **Vertex AI, BigQuery ML** |
| Edge computing | **Greengrass, well-documented outage buffering** | IoT Operations on Arc/Kubernetes | Partner edge only |
| Security | X.509 identities, Mumbai region | OT-grade PKI, Defender for IoT | Data pinned to India regions |
| Scalability | Very high | Very high | Very high |
| Integration | SAP via AppFlow | **Microsoft 365, Entra, Power BI, SAP** | Best SAP connector |
| Ease of use | IIoT now a set of separate parts | Fabric SaaS, common Microsoft skills | BigQuery simple, edge is DIY |
| Indicative cost (edge design) | ₹43k a month | ₹80k a month | **₹33k a month** |

**What it means for the factory:**
- **Azure** offers the most complete current chain from old controllers to dashboards.
- **AWS** has the best-documented edge buffering.
- **GCP** has the cheapest and strongest analytics, but no factory-floor layer of its own.

## C. Weighted decision matrix (scores 1–5)

| Criterion | Weight | AWS | Azure | GCP |
|---|---|---|---|---|
| Industrial IoT & OT connectivity | 15 % | 4 | 5 | 2 |
| Indicative cost (INR) | 13 % | 4 | 2 | 5 |
| Edge computing & offline operation | 12 % | 4 | 4 | 2 |
| Security, compliance & India residency | 12 % | 4 | 4 | 3 |
| Time-series storage & data lake | 10 % | 4 | 5 | 4 |
| Stream processing & analytics | 10 % | 3 | 5 | 4 |
| AI/ML | 10 % | 5 | 4 | 5 |
| Integration (MES/ERP, Microsoft 365, OPC UA) | 8 % | 3 | 5 | 4 |
| Scalability | 5 % | 5 | 5 | 5 |
| Ease of use & skills | 5 % | 3 | 4 | 3 |
| **Weighted total** | **100 %** | **3.92** | **4.22** | **3.57** |

**Recommendation: Microsoft Azure (Central India, Pune), with an edge-first design.** The reasons come from the scenario, not only from the score:
- **Brownfield controllers:** the plants run old Fanuc and Siemens controllers that speak OPC UA, and Azure reads OPC UA natively.
- **Existing tools:** the plants already use Microsoft tools (Power BI, Microsoft 365).
- **Location:** the Azure region is in Pune, next to Chakan.
- **Weaknesses removed by design:** the edge layer removes Azure's cost and offline-time weaknesses.

**How robust the result is:**
- Azure wins every ±5-point weight shift and **88.7 % of 10,000 random re-weightings**.
- AWS wins only if cost carries at least 35 % of the weight.
- **Edge batching is the biggest cost lever:** sending one message per reading would cost ₹14–30 lakh a month, against ₹33k–80k a month with edge batching.

## D. SQL database design (PostgreSQL 16)

**Schema.** The main table is `core.machine_data`, with one row per machine per hour:
- the required columns: machine_id, ts, temperature, vibration, rpm, current, production_count, machine_status, alarm;
- extra columns: reject_count, alarm_code, tool_wear and running_minutes.

It references machine, plant, part and alarm master tables, and CHECK constraints reject impossible values. It holds **876,100 rows**. The same queries were re-run on **Google BigQuery** (Mumbai) and gave identical results.

| Question | Answer from the data |
|---|---|
| Average temperature per machine | 36.4–39.1 °C across the 100 machines (hobbing machines run hottest) |
| Machine with the most parts | **P3-TURN-05**: 199,677 brake discs |
| Highest average vibration | **P1-VMC-13**: 1.86 mm/s (ISO 10816 zone B, acceptable) |
| Alarms per machine | 4,680 alarm events in total; P1-HMC-22 has the most (75) |
| Parts on a selected day (16 Jun 2025) | 23,974 parts, 381 rejected |
| Longest operating duration | **P1-HMC-18**: 209 h without stopping |
| Average RPM while running | VMC 6,888 · HMC 5,334 · grinder 3,168 · turning 2,300 · hobbing 967 |
| Highest rejection rate | **P2-GRIND-06**: 1.97 % (finish-ground gear shafts) |

**Extra analytics:** fleet **OEE 75.3 %** (world-class is 85 %), MTBF/MTTR, alarm Pareto, and vibration anomalies that come before failures.

## E. GitHub repository

The repository is at **github.com/TirthankerSingh/industrial-data-platform**. Its structure follows the assignment: `data/`, `python/`, `sql/`, `dashboard/`, `diagrams/`, `README.md` and `report.pdf`.
- **README** covers the problem, scenario, datasets, libraries, run steps, SQL setup, key findings and architecture.
- **History** has descriptive commits (feat/fix/docs) built up in stages, one part at a time.
- **Secrets** (database passwords, cloud keys) are git-ignored and were never committed.

## F. Industrial cloud architecture (Azure)

| Block | Azure service (prototype component) |
|---|---|
| CNC / PLC / sensors | Fanuc / Siemens controllers + spindle accelerometer |
| OPC UA / MQTT | OPC UA connector; MQTT broker with an ISA-95 topic tree (enterprise / plant / area / machine) |
| Edge gateway | **Azure IoT Operations** on Arc-enabled Kubernetes: 42 features per second, 7-day store-and-forward buffer |
| Cloud ingestion | IoT Hub / Event Hubs → Fabric Eventstreams |
| Data lake / time-series | **ADLS Gen2 lakehouse** (bronze, silver, gold) + Fabric Eventhouse |
| SQL database | Azure Database for PostgreSQL (Flexible Server) (prototype: PostgreSQL 16 and Google BigQuery) |
| Python analytics / AI | Azure ML / Fabric notebooks (prototype: Isolation Forest, Random Forest) |
| Dashboard | Power BI (prototype: Streamlit, live) |
| Manufacturing decision | Maintenance before failure, tool changes based on condition, OEE improvement |

## G. Edge versus cloud

| At the edge | In the cloud |
|---|---|
| 2 kHz vibration processing into features | Historical and fleet-level analysis |
| Immediate alarms and local machine protection | Long-term storage (lakehouse) |
| Noise filtering and data aggregation | AI/ML model training and management |
| Store-and-forward buffering during outages | Management dashboards and remote access |

**Engineering justification:**
- **Latency:** machine protection needs millisecond responses, which the cloud cannot guarantee.
- **Reliability:** a plant must keep running when its internet link fails. Our gateway test lost **0 of 482 messages** through two outages.
- **Bandwidth:** sending features instead of raw signals cuts the data 143×.
- **Cost:** the cloud bill stays at ₹33k–80k a month instead of lakhs.
- **Cybersecurity:** the OT network makes only outbound, encrypted connections, following IEC 62443 zones.
- **Scalability:** adding a plant means adding another identical edge node.

**The cloud** is where scale pays off: the full fleet history, model training and dashboards for the whole company.

## Storage pattern and results

**Storage pattern:** a lakehouse, chosen over a pure lake or a pure warehouse.
- Over 99 % of the bytes are raw vibration, which belongs in a cheap lake.
- Clean, de-duplicated tables serve dashboards and AI from the same copy of the data.

**Results:**
- **Bosch anomaly detection:** ROC-AUC **0.98**, holding when trained on 2019 data and tested on 2021.
- **24-hour failure warning:** works on the benchmark data. It scores almost perfectly only because that data is simulated.
- **Estimated business value:** about **₹5.8 crore a year**.
- **Live dashboard:** reads Google BigQuery in Mumbai through a read-only service account. If BigQuery is unavailable, it falls back to a Parquet snapshot.
