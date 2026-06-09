# ☀️ Solar OS — Autonomous Solar Farm Intelligence

> AI-powered edge decision engine that autonomously manages solar farms — protecting panels, optimizing energy conversion, and deciding in real-time whether to store, convert to hydrogen, or distribute energy.

---

## 🚀 Live Demo

**[https://solar-os-ai.streamlit.app](https://solar-os-ai.streamlit.app)**

---

## 🎯 Built For

**Tata Technologies InnoVent-27 Hackathon**  
**Category:** Edge AI for Sustainable & Energy-Efficient Industrial Systems

---

## 🚨 Problem

- Solar farms are **passive assets** — panels sit exposed to storms, birds, and dust with no unified intelligence to protect or optimize them in real time.
- **Fragmented tooling** — weather APIs, battery management, CV, and grid software operate in silos with no single decision brain.
- **Unpredictable output** makes grid operators distrust solar — massive efficiency loss and missed revenue during peak pricing windows.

---

## 💡 Solution

Solar OS replaces dumb panels with an **autonomous edge decision loop**:

```
Sense → Decide → Act → Store/Convert → Distribute
```

One AI brain that senses threats, decides autonomously, protects panels, converts surplus to H₂, and syncs decisions to the cloud — with minimal human intervention.

---

## ✅ Features

### 🏠 Home — Fleet Overview
- Real-time weather metrics (temperature, wind, rain, solar output)
- AI system status banner (harvest / store / protect / distribute)
- **Farm Health Score** (0–100) with live progress bar
- Edge vs Cloud mode indicator
- **HiveMQ Cloud** live MQTT publish on every refresh

### 🛡️ Shield — Protection + CV Detection
- Autonomous shield system (OPEN / STANDBY / CLOSED)
- Threat breakdown (storm, rain, wind, bird, dust)
- **YOLOv8n** computer vision module with 9 sample images
- Filename-based demo override + real inference on uploads
- Colored threat borders (red / orange / yellow)

### ⚡ Energy — Storage & Harvesting
- Solar radiation forecast chart
- Battery + H₂ tank status with AI storage routing
- Hydrogen generation simulation
- 24-hour AI decision log (hour-by-hour)

### 📅 Forecast — 7-Day AI Plan
- 7-day weather + solar forecast table
- Per-day AI operational plan
- Real-time alert system (critical / high / medium / low)
- Upcoming storm and rain pre-warnings

### 💰 Analytics — ROI & Reports
- Energy savings calculator (daily / annual / diesel displaced)
- Efficiency loss tracker (dust, bird, heat recovery)
- 25-year fossil vs solar cost comparison
- Geopolitical energy independence panel
- **📄 PDF Farm Report** download (branded 5-page ReportLab export)

### 🖥️ Edge Node — RPi4 Simulation
- Edge mode toggle (RPi4-ARM64 vs Cloud)
- Inference latency, CPU, memory, uptime metrics
- Recent edge decision log
- **MQTT feed** (local Mosquitto or session-state mock)
- **HiveMQ Cloud** live status
- **Mobile Alert System** (AWS SNS mock + Gmail SMTP)
- Mock phone notification UI

### 🌍 Multi-Farm — India Fleet Dashboard
- 5 Indian solar farms (Jaisalmer, Jodhpur, Kutch, Anantapur, Tumkur)
- **Plotly India map** with dark/terrain toggle
- Threat-colored markers sized by health score
- Fleet summary metrics + solar output comparison chart
- Per-farm detail panel with 24hr decision log

### ⚡ Grid Export — Revenue Optimization
- Time-of-day pricing (peak / normal / off-peak)
- AI export recommendation (EXPORT NOW / STORE / BUY FROM GRID)
- 24-hour export plan table with expected revenue
- Dual-axis price vs solar chart with export windows
- Grid Stability Score metric

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Edge Runtime | Python 3.11, AWS IoT Greengrass simulation |
| CV Module | YOLOv8n (Ultralytics) |
| Weather API | Open-Meteo (free, no key) |
| Dashboard | Streamlit + Plotly |
| IoT Broker | HiveMQ Cloud (real MQTT over TLS) |
| Alerts | SMTP Gmail + AWS SNS mock |
| PDF Reports | ReportLab |
| Deployment | Streamlit Cloud |

---

## 📸 Screenshots

> Add screenshots to `/docs/screenshots/` and replace placeholders below.

### Home Dashboard
![Home Dashboard](docs/screenshots/home.png)
*Real-time metrics, Farm Health Score, HiveMQ status, and AI decision banner.*

### Shield + CV Detection
![Shield + CV Detection](docs/screenshots/shield-cv.png)
*Autonomous shield system with YOLOv8 threat detection on solar panel images.*

### Multi-Farm India Map
![Multi-Farm Map](docs/screenshots/multi-farm.png)
*Fleet-wide Plotly map across 5 Indian solar zones with health-scored markers.*

### Grid Export
![Grid Export](docs/screenshots/grid-export.png)
*Time-of-day pricing optimization with AI export recommendations.*

### Edge Node + MQTT
![Edge Node](docs/screenshots/edge-node.png)
*RPi4 edge simulation, HiveMQ feed, and mobile alert system.*

---

## 🚀 Run Locally

```bash
git clone https://github.com/ayushanand27/solar-getdone.git
cd solar-getdone
pip install -r requirements.txt
streamlit run app.py
```

### Optional: Secrets Setup

Create `.streamlit/secrets.toml` (not committed to git):

```toml
[email]
sender = "your-gmail@gmail.com"
password = "your-app-password"
recipient = "your-email@gmail.com"

[mqtt]
host = "your-broker.hivemq.cloud"
port = 8883
username = "your-username"
password = "your-password"
```

---

## 📁 Project Structure

```
solar/
├── app.py                      # Home — metrics, health score, HiveMQ publish
├── pages/
│   ├── 1_🛡️_Shield.py          # Shield system + YOLOv8 CV detection
│   ├── 2_⚡_Energy.py           # Battery, H₂, radiation, 24hr decision log
│   ├── 3_📅_Forecast.py         # 7-day forecast + real-time alerts
│   ├── 4_💰_Analytics.py        # Savings, ROI, PDF report download
│   ├── 5_🖥️_Edge_Node.py        # Edge monitor, MQTT, mobile alerts
│   ├── 6_🌍_Multi_Farm.py       # 5-farm India fleet dashboard + map
│   └── 7_⚡_Grid_Export.py      # Grid export optimization
├── utils/
│   ├── ai_engine.py            # Autonomous decision logic
│   ├── app_state.py            # Shared sidebar + session state
│   ├── cv_module.py            # YOLOv8 computer vision
│   ├── email_alerts.py         # Gmail SMTP alerts
│   ├── health_score.py         # Farm health scoring (0–100)
│   ├── mobile_alerts.py        # SNS mock + alert log
│   ├── mqtt_client.py          # HiveMQ Cloud publisher
│   ├── mqtt_sim.py             # Local MQTT simulation
│   ├── pdf_report.py           # Branded PDF report generator
│   └── weather.py              # Open-Meteo API calls
├── sample/                     # CV demo images (bird, dust, crack)
├── requirements.txt
└── README.md
```

---

## 🌍 Impact

| Metric | Value |
|---|---|
| Efficiency recovery with Solar OS | **15%** |
| Edge decision latency | **< 100 ms** |
| Annual savings (10 MW farm) | **₹90L / year** |
| H₂ production per farm | **52 kg / day** |

> *"The sun sends Earth enough energy in 1 hour to power all of humanity for a year. We capture less than 1% of it."*

Solar OS is a step toward energy sovereignty — starting with making existing farms smarter, protected, and grid-ready.

---

## 👨‍💻 Built By

**Ayush Anand** | CSE (IoT & Intelligent Systems)  
Manipal University Jaipur | 3rd Year  
PwC Advisory Launchpad Trainee

Building in public for **InnoVent-27**. No investors. No pitch decks. Just shipping.

---

## ⭐ Star this repo

If you believe in **energy independence**, **edge AI for renewables**, and **smarter solar farms** — star this repo and share it with your network.

---

<p align="center">
  <b>☀️ Solar OS v1.0</b> — Sense. Decide. Act. Distribute.
</p>
