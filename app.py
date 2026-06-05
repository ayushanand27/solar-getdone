import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time
import random

st.set_page_config(page_title="Solar OS", layout="wide", page_icon="☀️")

# --- SIDEBAR ---
st.sidebar.title("📍 Location")
city = st.sidebar.text_input("Enter City", value="Jaipur")

st.sidebar.divider()
st.sidebar.title("🧪 Threat Simulator")
auto_sim = st.sidebar.toggle("⚡ Auto Simulation", value=False)
st.sidebar.caption("Auto generates random threat events every 5s")
bird_btn = st.sidebar.button("🐦 Bird Attack", use_container_width=True)
dust_btn = st.sidebar.button("🌫️ Dust Storm", use_container_width=True)

# Sim event
if bird_btn:
    sim_event = "bird"
elif dust_btn:
    sim_event = "dust"
elif auto_sim:
    random.seed(int(time.time()) // 5)
    sim_event = random.choice([None, None, None, "bird", "dust", "bird", "dust"])
else:
    sim_event = None

if sim_event == "bird":
    st.sidebar.error("🐦 Bird activity detected!")
elif sim_event == "dust":
    st.sidebar.error("🌫️ Dust storm detected!")
else:
    st.sidebar.success("✅ No simulated threats")

# --- COORDINATES ---
@st.cache_data(ttl=3600)
def get_coordinates(city):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    r = requests.get(url)
    data = r.json()
    if "results" in data and len(data["results"]) > 0:
        return data["results"][0]["latitude"], data["results"][0]["longitude"], data["results"][0]["name"]
    return 26.9124, 75.7873, "Jaipur"

lat, lon, city_name = get_coordinates(city)
st.sidebar.success(f"📍 Showing data for: {city_name}")

# --- TITLE ---
st.title("☀️ Solar OS — Autonomous Solar Farm Intelligence")
st.caption(f"Real-time AI decision engine | 📍 {city_name}")

# --- FETCH WEATHER ---
@st.cache_data(ttl=300)
def get_weather(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,weathercode,windspeed_10m,precipitation"
        f"&hourly=shortwave_radiation"
        f"&forecast_days=1"
    )
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if "current" not in data:
            raise ValueError("No current data")
        return data
    except Exception:
        return {
            "current": {"temperature_2m": 30, "weathercode": 0, "windspeed_10m": 10, "precipitation": 0},
            "hourly": {
                "shortwave_radiation": [0,0,0,0,0,10,50,120,180,200,195,185,160,120,80,40,10,0,0,0,0,0,0,0],
                "time": [f"2026-06-05T{h:02d}:00" for h in range(24)]
            }
        }

data = get_weather(lat, lon)
current = data["current"]
hourly = data["hourly"]

temp = current["temperature_2m"]
wind = current["windspeed_10m"]
rain = current["precipitation"]
wcode = current["weathercode"]
radiation = hourly["shortwave_radiation"]
hours = hourly["time"]

# --- AI Decision Engine ---
def ai_decision(wcode, wind, rain, radiation, sim_event):
    hr = min(datetime.now().hour, len(radiation)-1)
    solar_output = round(radiation[hr] * 0.22, 1)

    if wcode >= 95:
        return "🛡️ SHIELD CLOSED", "Thunderstorm detected — panels protected", "protection", solar_output, "CLOSED", "Thunderstorm detected", "CRITICAL"
    elif wcode >= 61 or rain > 0.5:
        return "🛡️ SHIELD CLOSED", "Heavy rain — panels protected", "protection", solar_output, "CLOSED", "Heavy rainfall detected", "HIGH"
    elif wind > 60:
        return "🛡️ SHIELD CLOSED", "Extreme wind — panels protected", "protection", solar_output, "CLOSED", "Extreme wind speed", "HIGH"
    elif wind > 40:
        return "⚠️ MONITORING", "High wind — monitoring closely", "monitor", solar_output, "READY", "Wind speed elevated — shield on standby", "MEDIUM"
    elif sim_event == "bird":
        return "🛡️ SHIELD PARTIAL", "Bird activity — deterrent active, partial shield", "monitor", solar_output, "READY", "Bird swarm detected by camera", "MEDIUM"
    elif sim_event == "dust":
        return "⚠️ DUST ALERT", "Dust storm — auto-clean sequence triggered", "monitor", solar_output, "READY", "Dust levels critical", "MEDIUM"
    elif solar_output > 150:
        return "⚡ FULL CONVERSION", "Peak sunlight — maximum energy harvesting", "harvest", solar_output, "OPEN", "Clear sky — full exposure", "LOW"
    elif solar_output > 50:
        return "🔋 STORING + H₂", "Moderate sunlight — storing battery + making hydrogen", "store", solar_output, "OPEN", "Normal conditions", "LOW"
    else:
        return "🌙 DISTRIBUTING", "Low/no sunlight — distributing stored energy", "distribute", solar_output, "OPEN", "No threat detected", "LOW"

status, action, mode, solar_output, shield, shield_reason, threat_level = ai_decision(wcode, wind, rain, radiation, sim_event)

# --- TOP METRICS ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("🌡️ Temperature", f"{temp}°C")
col2.metric("💨 Wind Speed", f"{wind} km/h")
col3.metric("🌧️ Precipitation", f"{rain} mm")
col4.metric("☀️ Solar Output", f"{solar_output} W/m²")
st.divider()

# --- SYSTEM STATUS ---
if mode == "protection": st.error(f"**{status}** — {action}")
elif mode == "harvest": st.success(f"**{status}** — {action}")
elif mode == "monitor": st.warning(f"**{status}** — {action}")
elif mode == "store": st.warning(f"**{status}** — {action}")
else: st.info(f"**{status}** — {action}")
st.divider()

# --- SHIELD STATUS ---
st.subheader("🛡️ Shield Protection System")
s1, s2, s3 = st.columns(3)
with s1:
    if shield == "CLOSED":
        st.error(f"### 🔒 SHIELD: CLOSED\n**Reason:** {shield_reason}\n\nPanels fully protected.")
    elif shield == "READY":
        st.warning(f"### ⚠️ SHIELD: STANDBY\n**Reason:** {shield_reason}\n\nShield ready to deploy.")
    else:
        st.success(f"### ✅ SHIELD: OPEN\n**Reason:** {shield_reason}\n\nMaximum harvesting active.")

with s2:
    st.markdown("### 🎯 Threat Assessment")
    if threat_level == "CRITICAL": st.error("🔴 CRITICAL THREAT"); st.progress(100)
    elif threat_level == "HIGH": st.error("🟠 HIGH THREAT"); st.progress(75)
    elif threat_level == "MEDIUM": st.warning("🟡 MEDIUM THREAT"); st.progress(50)
    else: st.success("🟢 LOW THREAT"); st.progress(15)
    st.caption(f"Weather code: {wcode} | Wind: {wind} km/h | Rain: {rain}mm")

with s3:
    st.markdown("### 📋 Threat Breakdown")
    threats = {
        "⛈️ Thunderstorm": "🔴 YES" if wcode >= 95 else "🟢 NO",
        "🌧️ Heavy Rain": "🔴 YES" if rain > 0.5 else "🟢 NO",
        "💨 Extreme Wind": "🔴 YES" if wind > 60 else "🟢 NO",
        "⚠️ High Wind": "🟡 WATCH" if 40 < wind <= 60 else "🟢 NO",
        "🌫️ Dust Storm": "🔴 YES" if sim_event == "dust" else "🟢 NO",
        "🐦 Bird Activity": "🔴 YES" if sim_event == "bird" else "🟢 NO",
    }
    for t, v in threats.items():
        st.markdown(f"{t} — **{v}**")
st.divider()

# --- SOLAR RADIATION CHART ---
st.subheader("☀️ Today's Solar Radiation Forecast")
df = pd.DataFrame({"Time": hours, "Radiation (W/m²)": radiation})
df["Estimated Output (W/m²)"] = df["Radiation (W/m²)"] * 0.22
if sim_event == "dust":
    df["Estimated Output (W/m²)"] = df["Estimated Output (W/m²)"] * 0.75
    st.caption("⚠️ Dust storm active — showing 25% efficiency loss")
st.line_chart(df.set_index("Time")["Estimated Output (W/m²)"])

# --- HYDROGEN SIMULATION ---
st.subheader("🧪 Hydrogen Storage Simulation")
h2_stored = round(sum([r * 0.22 * 0.7 for r in radiation if r > 100]) / 1000, 2)
st.metric("Estimated H₂ Generated Today", f"{h2_stored} kg")
st.caption("Based on today's radiation forecast × panel efficiency × electrolysis efficiency")
st.divider()
st.caption("🔄 Data refreshes every 5 minutes automatically")

# --- BATTERY + H2 STORAGE ---
st.divider()
st.subheader("🔋 Energy Storage System")
b1, b2, b3 = st.columns(3)
battery_level = min(100, int(solar_output / 2))
h2_level = min(100, int(h2_stored * 40))

with b1:
    st.markdown("### 🔋 Battery Status")
    st.progress(battery_level / 100)
    st.metric("Charge Level", f"{battery_level}%")
    if battery_level > 80: st.warning("Battery nearly full → switching to H₂ mode")
    elif battery_level > 30: st.success("Battery charging normally")
    else: st.error("Battery low — prioritizing charging")

with b2:
    st.markdown("### 🧪 H₂ Tank Status")
    st.progress(h2_level / 100)
    st.metric("Tank Level", f"{h2_level}%")
    if h2_level > 80: st.warning("H₂ tank nearly full")
    elif h2_level > 20: st.success("H₂ production active")
    else: st.info("H₂ tank empty — building up")

with b3:
    st.markdown("### 🤖 AI Storage Decision")
    if battery_level > 80 and h2_level < 80: st.warning("→ Redirecting to H₂ conversion")
    elif battery_level < 30: st.error("→ Priority: Charge battery first")
    elif h2_level > 80 and battery_level > 80: st.success("→ Both full: Export to grid")
    else: st.success("→ Normal: Battery + H₂ parallel")
    st.caption(f"Battery: {battery_level}% | H₂: {h2_level}% | Solar: {solar_output} W/m²")

# --- 24HR AI DECISION LOG ---
st.divider()
st.subheader("🤖 24hr AI Decision Log")
log_rows = []
for i, (h, r) in enumerate(zip(hours, radiation)):
    hour_output = round(r * 0.22 * (0.75 if sim_event == "dust" else 1), 1)
    if hour_output > 150: decision, sh = "⚡ Full Conversion", "🟢 Open"
    elif hour_output > 50: decision, sh = "🔋 Store + H₂", "🟢 Open"
    else: decision, sh = "🌙 Distribute", "🟢 Open"
    if sim_event == "bird": sh = "⚠️ Partial"
    log_rows.append({"Hour": h[11:16], "Solar Output (W/m²)": hour_output, "AI Decision": decision, "Shield": sh})
st.dataframe(pd.DataFrame(log_rows), use_container_width=True, hide_index=True)

# --- ENERGY SAVINGS CALCULATOR ---
st.divider()
st.subheader("💰 Energy Savings Calculator")
st.caption("If Solar OS was managing a real farm here — what would be saved?")
ec1, ec2, ec3 = st.columns(3)
with ec1: farm_size = st.slider("Farm Size (kW)", 10, 10000, 500, 10)
with ec2: electricity_rate = st.slider("Electricity Rate (₹/kWh)", 3, 12, 7)
with ec3: diesel_rate = st.slider("Diesel Price (₹/L)", 80, 120, 95)

daily_hours = sum(1 for r in radiation if r * 0.22 > 50)
daily_energy_kwh = round(farm_size * daily_hours * 0.22, 1)
annual_energy_kwh = round(daily_energy_kwh * 365, 1)
annual_savings_inr = round(annual_energy_kwh * electricity_rate, 0)
diesel_displaced_litres = round(annual_energy_kwh / 3.5, 1)
co2_saved_kg = round(annual_energy_kwh * 0.82, 1)

r1, r2, r3, r4 = st.columns(4)
r1.metric("⚡ Daily Energy", f"{daily_energy_kwh} kWh")
r2.metric("📅 Annual Energy", f"{annual_energy_kwh:,} kWh")
r3.metric("💰 Annual Savings", f"₹{annual_savings_inr:,.0f}")
r4.metric("🌿 CO₂ Saved", f"{co2_saved_kg:,} kg/year")
st.divider()
d1, d2 = st.columns(2)
d1.metric("🛢️ Diesel Displaced", f"{diesel_displaced_litres:,} litres/year")
d2.metric("💵 Diesel Cost Saved", f"₹{round(diesel_displaced_litres * diesel_rate):,}/year")
st.caption(f"Based on {daily_hours} productive solar hours × {farm_size}kW × ₹{electricity_rate}/kWh")

# --- 7-DAY FORECAST ---
st.divider()
st.subheader("📅 7-Day Solar Forecast + AI Plan")

@st.cache_data(ttl=3600)
def get_7day(lat, lon):
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
           f"&daily=weathercode,shortwave_radiation_sum,precipitation_sum,windspeed_10m_max"
           f"&forecast_days=7&timezone=auto")
    try:
        r = requests.get(url, timeout=10)
        return r.json()
    except:
        return {"daily": {"weathercode":[0]*7,"shortwave_radiation_sum":[5000]*7,
                          "precipitation_sum":[0]*7,"windspeed_10m_max":[15]*7,
                          "time":[f"2026-06-0{i+3}" for i in range(7)]}}

forecast = get_7day(lat, lon)
days = forecast["daily"]
day_rows = []
for i in range(7):
    wc = days["weathercode"][i]
    rad = days["shortwave_radiation_sum"][i]
    prec = days["precipitation_sum"][i]
    wind_max = days["windspeed_10m_max"][i]
    date = days["time"][i]
    est_output = round(rad * 0.22, 1) if rad else 0
    if wc >= 95: ai_plan, rec = "🛡️ Shield closed all day", "🔴 Storm — protect panels"
    elif wc >= 61 or prec > 2: ai_plan, rec = "🛡️ Shield closed — rain", "🟠 Rain — minimal harvest"
    elif est_output > 3000: ai_plan, rec = "⚡ Full harvest + H₂ store", "🟢 Excellent day — max production"
    elif est_output > 1000: ai_plan, rec = "🔋 Normal harvest + store", "🟡 Good day — normal ops"
    else: ai_plan, rec = "🌙 Distribute stored energy", "⚪ Low solar — use reserves"
    day_rows.append({"Date": date, "Est. Output (Wh/m²)": est_output, "Rain (mm)": prec,
                     "Max Wind (km/h)": wind_max, "AI Plan": ai_plan, "Status": rec})

day_df = pd.DataFrame(day_rows)
st.dataframe(day_df, use_container_width=True, hide_index=True)
best_day = day_df.loc[day_df["Est. Output (Wh/m²)"].idxmax(), "Date"]
worst_day = day_df.loc[day_df["Est. Output (Wh/m²)"].idxmin(), "Date"]
storm_days = day_df[day_df["Rain (mm)"] > 2].shape[0]
st.info(f"🤖 **AI Weekly Insight:** Best day → **{best_day}** | Storm days → **{storm_days}** | Low day → **{worst_day}** — pre-charge batteries!")

# --- ALERT SYSTEM ---
st.divider()
st.subheader("🚨 Real-Time Alert System")
alerts = []
if wcode >= 95: alerts.append(("CRITICAL", "⛈️ THUNDERSTORM", f"Shield closed. Location: {city_name}"))
if wcode >= 61 or rain > 0.5: alerts.append(("HIGH", "🌧️ HEAVY RAINFALL", f"Rain: {rain}mm. Panels protected."))
if wind > 60: alerts.append(("HIGH", "💨 EXTREME WIND", f"{wind} km/h — shield closed."))
if wind > 40: alerts.append(("MEDIUM", "⚠️ HIGH WIND", f"{wind} km/h — standby."))
if solar_output < 10 and 7 < datetime.now().hour < 17:
    alerts.append(("MEDIUM", "☁️ LOW SOLAR", f"Only {solar_output} W/m² during daylight."))
if sim_event == "bird": alerts.append(("HIGH", "🐦 BIRD DETECTED", "Deterrent active. Shield partially closing."))
if sim_event == "dust": alerts.append(("HIGH", "🌫️ DUST STORM", "25% efficiency drop. Auto-clean initiated."))
for row in day_rows:
    if "Storm" in row["Status"] or "Rain" in row["Status"]:
        alerts.append(("LOW", f"📅 UPCOMING: {row['Date']}", f"{row['AI Plan']} — Pre-charge batteries."))

if not alerts:
    st.success("✅ All systems normal — No active alerts")
else:
    for level, title, msg in alerts:
        if level == "CRITICAL": st.error(f"🔴 **{title}**\n\n{msg}")
        elif level == "HIGH": st.error(f"🟠 **{title}**\n\n{msg}")
        elif level == "MEDIUM": st.warning(f"🟡 **{title}**\n\n{msg}")
        else: st.info(f"🔵 **{title}**\n\n{msg}")
st.caption(f"Last checked: {datetime.now().strftime('%H:%M:%S')} | {city_name}")

# --- EFFICIENCY LOSS TRACKER ---
st.divider()
st.subheader("📉 Efficiency Loss Tracker")
st.caption("Real cost of NOT having Solar OS")
el1, el2, el3, el4 = st.columns(4)
dust_loss = round(solar_output * 0.28, 1)
bird_loss = round(solar_output * 0.05, 1)
temp_loss = round(max(0, (temp - 25) * 0.004 * solar_output), 1)
total_loss = round(dust_loss + bird_loss + temp_loss, 1)
protected_output = round(solar_output + total_loss, 1)
el1.metric("🌫️ Dust Loss", f"{dust_loss} W/m²", "-28% typical")
el2.metric("🐦 Bird Loss", f"{bird_loss} W/m²", "-5% typical")
el3.metric("🌡️ Heat Loss", f"{temp_loss} W/m²", f"Temp: {temp}°C")
el4.metric("💡 With Solar OS", f"{protected_output} W/m²", f"+{total_loss} recovered")
recovery_pct = round(total_loss / max(protected_output, 1) * 100, 1)
st.info(f"🤖 Without Solar OS: **{solar_output} W/m²** | With Solar OS: **{protected_output} W/m²** | Recovery: **{recovery_pct}%**")

# --- GEOPOLITICAL PANEL ---
st.divider()
st.subheader("🌍 Geopolitical Energy Independence")
st.caption("Why this matters beyond electricity bills")
g1, g2 = st.columns(2)
with g1:
    st.markdown("""
### 🛢️ Current Reality
- **20%** of world oil passes through Strait of Hormuz
- **1 conflict** → global fuel prices spike instantly
- India imports **96%** of its crude oil
- Bangladesh, Philippines — economies collapse on fuel shock
- Solar exists but is **poorly managed** — massive waste
    """)
with g2:
    st.markdown("""
### ☀️ Solar OS Reality
- Sun sends enough energy in **1 hour** to power humanity for 1 year
- We capture **< 1%** of available solar energy
- Solar OS maximizes what we DO capture
- Every optimized farm = less oil dependency
- **Energy sovereignty** — your own remote control
    """)
oil_saved = round(diesel_displaced_litres / 1000, 1)
st.success(f"🌍 This {farm_size}kW farm managed by Solar OS saves **{oil_saved}K litres** of oil/year — direct geopolitical independence.")

# --- WHY SOLAR OS ---
st.divider()
st.subheader("🚀 Why Solar OS Exists")
w1, w2, w3 = st.columns(3)
with w1:
    st.error("""
### ❌ Problem Today
Solar farms are **dumb**

- Panels just sit there
- No unified AI brain
- Separate vendors for everything
- Human monitors 24/7
- Threats damage panels daily
- Unpredictable → grid rejects solar
    """)
with w2:
    st.warning("""
### ⚙️ What Exists
Fragmented solutions

- Cleaning robots (separate)
- Weather APIs (separate)
- Battery management (separate)
- Grid software (separate)
- No system talks to another
- SpaceX model missing in solar
    """)
with w3:
    st.success("""
### ✅ Solar OS Vision
One AI brain for everything

- Sense all threats real-time
- Decide autonomously
- Protect, clean, convert, store
- Predict & plan 7 days ahead
- Tell grid exactly what's coming
- Minimal human intervention
    """)

# --- FOSSIL vs SOLAR COMPARISON ---
st.divider()
st.subheader("⚖️ Solar OS vs Fossil Fuel — 25 Year Cost")
years = list(range(1, 26))
fossil_cost = [farm_size * 0.12 * 8760 * y for y in years]
solar_cost_cumulative = [farm_size * 500 + (farm_size * 0.02 * 8760 * y) for y in years]
comp_df = pd.DataFrame({"Year": years, "Fossil Fuel Cost (₹)": fossil_cost, "Solar OS Cost (₹)": solar_cost_cumulative})
st.line_chart(comp_df.set_index("Year"))
breakeven = next((y for y, f, s in zip(years, fossil_cost, solar_cost_cumulative) if s < f), None)
if breakeven:
    st.success(f"💰 Solar OS breaks even at **Year {breakeven}** — then **{25-breakeven} years of pure savings.**")
st.caption("Based on ₹12/kWh fossil cost vs ₹500/kW solar installation + ₹2/kWh maintenance")

# Auto refresh
if auto_sim:
    time.sleep(5)
    st.rerun()