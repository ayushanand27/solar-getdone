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

st.sidebar.markdown("**Manual Triggers:**")
bird_btn = st.sidebar.button("🐦 Bird Attack", use_container_width=True)
dust_btn = st.sidebar.button("🌫️ Dust Storm", use_container_width=True)

# Determine sim event
if bird_btn:
    sim_event = "bird"
elif dust_btn:
    sim_event = "dust"
elif auto_sim:
    sim_time = int(time.time()) // 5
    random.seed(sim_time)
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
    if "results" in data:
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
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weathercode,windspeed_10m,precipitation&hourly=shortwave_radiation&forecast_days=1"
    r = requests.get(url)
    return r.json()

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
    solar_output = round(radiation[datetime.now().hour] * 0.22, 1)

    if wcode >= 95:
        status = "🛡️ SHIELD CLOSED"; action = "Thunderstorm detected — panels protected"
        mode = "protection"; shield = "CLOSED"; shield_reason = "Thunderstorm detected"; threat_level = "CRITICAL"
    elif wcode >= 61 or rain > 0.5:
        status = "🛡️ SHIELD CLOSED"; action = "Heavy rain — panels protected"
        mode = "protection"; shield = "CLOSED"; shield_reason = "Heavy rainfall detected"; threat_level = "HIGH"
    elif wind > 60:
        status = "🛡️ SHIELD CLOSED"; action = "Extreme wind — panels protected"
        mode = "protection"; shield = "CLOSED"; shield_reason = "Extreme wind speed"; threat_level = "HIGH"
    elif wind > 40:
        status = "⚠️ MONITORING"; action = "High wind — monitoring closely"
        mode = "monitor"; shield = "READY"; shield_reason = "Wind speed elevated — shield on standby"; threat_level = "MEDIUM"
    elif sim_event == "bird":
        status = "🛡️ SHIELD PARTIAL"; action = "Bird activity — deterrent active, partial shield"
        mode = "monitor"; shield = "READY"; shield_reason = "Bird swarm detected by camera"; threat_level = "MEDIUM"
    elif sim_event == "dust":
        status = "⚠️ DUST ALERT"; action = "Dust storm — auto-clean sequence triggered"
        mode = "monitor"; shield = "READY"; shield_reason = "Dust levels critical"; threat_level = "MEDIUM"
    elif solar_output > 150:
        status = "⚡ FULL CONVERSION"; action = "Peak sunlight — maximum energy harvesting"
        mode = "harvest"; shield = "OPEN"; shield_reason = "Clear sky — full exposure"; threat_level = "LOW"
    elif solar_output > 50:
        status = "🔋 STORING + H₂"; action = "Moderate sunlight — storing battery + making hydrogen"
        mode = "store"; shield = "OPEN"; shield_reason = "Normal conditions"; threat_level = "LOW"
    else:
        status = "🌙 DISTRIBUTING"; action = "Low/no sunlight — distributing stored energy"
        mode = "distribute"; shield = "OPEN"; shield_reason = "No threat detected"; threat_level = "LOW"

    return status, action, mode, solar_output, shield, shield_reason, threat_level

status, action, mode, solar_output, shield, shield_reason, threat_level = ai_decision(wcode, wind, rain, radiation, sim_event)

# --- TOP METRICS ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("🌡️ Temperature", f"{temp}°C")
col2.metric("💨 Wind Speed", f"{wind} km/h")
col3.metric("🌧️ Precipitation", f"{rain} mm")
col4.metric("☀️ Solar Output", f"{solar_output} W/m²")

st.divider()

# --- SYSTEM STATUS ---
if mode == "protection":
    st.error(f"**{status}** — {action}")
elif mode == "harvest":
    st.success(f"**{status}** — {action}")
elif mode in ["monitor"]:
    st.warning(f"**{status}** — {action}")
elif mode == "store":
    st.warning(f"**{status}** — {action}")
else:
    st.info(f"**{status}** — {action}")

st.divider()

# --- SHIELD STATUS PANEL ---
st.subheader("🛡️ Shield Protection System")
s1, s2, s3 = st.columns(3)

with s1:
    if shield == "CLOSED":
        st.error(f"### 🔒 SHIELD: CLOSED\n**Reason:** {shield_reason}\n\nPanels fully protected. No harvesting active.")
    elif shield == "READY":
        st.warning(f"### ⚠️ SHIELD: STANDBY\n**Reason:** {shield_reason}\n\nShield ready to deploy. Partial harvesting active.")
    else:
        st.success(f"### ✅ SHIELD: OPEN\n**Reason:** {shield_reason}\n\nPanels fully exposed. Maximum harvesting active.")

with s2:
    st.markdown("### 🎯 Threat Assessment")
    if threat_level == "CRITICAL":
        st.error("🔴 CRITICAL THREAT"); st.progress(100)
    elif threat_level == "HIGH":
        st.error("🟠 HIGH THREAT"); st.progress(75)
    elif threat_level == "MEDIUM":
        st.warning("🟡 MEDIUM THREAT"); st.progress(50)
    else:
        st.success("🟢 LOW THREAT"); st.progress(15)
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
    for threat, val in threats.items():
        st.markdown(f"{threat} — **{val}**")

st.divider()

# --- SOLAR RADIATION CHART ---
st.subheader("☀️ Today's Solar Radiation Forecast")
df = pd.DataFrame({"Time": hours, "Radiation (W/m²)": radiation})
df["Estimated Output (W/m²)"] = df["Radiation (W/m²)"] * 0.22

# Apply dust efficiency loss
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
    if battery_level > 80:
        st.warning("Battery nearly full → switching to H₂ mode")
    elif battery_level > 30:
        st.success("Battery charging normally")
    else:
        st.error("Battery low — prioritizing charging")

with b2:
    st.markdown("### 🧪 H₂ Tank Status")
    st.progress(h2_level / 100)
    st.metric("Tank Level", f"{h2_level}%")
    if h2_level > 80:
        st.warning("H₂ tank nearly full")
    elif h2_level > 20:
        st.success("H₂ production active")
    else:
        st.info("H₂ tank empty — building up")

with b3:
    st.markdown("### 🤖 AI Storage Decision")
    if battery_level > 80 and h2_level < 80:
        st.warning("→ Redirecting to H₂ conversion")
    elif battery_level < 30:
        st.error("→ Priority: Charge battery first")
    elif h2_level > 80 and battery_level > 80:
        st.success("→ Both full: Export to grid")
    else:
        st.success("→ Normal: Battery + H₂ parallel")
    st.caption(f"Battery: {battery_level}% | H₂: {h2_level}% | Solar: {solar_output} W/m²")

# --- 24HR AI DECISION LOG ---
st.divider()
st.subheader("🤖 24hr AI Decision Log")

log_rows = []
for i, (h, r) in enumerate(zip(hours, radiation)):
    hour_output = round(r * 0.22, 1)
    if sim_event == "dust":
        hour_output = round(hour_output * 0.75, 1)
    if hour_output > 150:
        decision = "⚡ Full Conversion"; sh = "🟢 Open"
    elif hour_output > 50:
        decision = "🔋 Store + H₂"; sh = "🟢 Open"
    else:
        decision = "🌙 Distribute"; sh = "🟢 Open"
    if sim_event == "bird":
        sh = "⚠️ Partial"
    log_rows.append({"Hour": h[11:16], "Solar Output (W/m²)": hour_output, "AI Decision": decision, "Shield": sh})

log_df = pd.DataFrame(log_rows)
st.dataframe(log_df, use_container_width=True, hide_index=True)

# --- ENERGY SAVINGS CALCULATOR ---
st.divider()
st.subheader("💰 Energy Savings Calculator")
st.caption("If Solar OS was managing a real farm here — what would be saved?")

ec1, ec2, ec3 = st.columns(3)
with ec1:
    farm_size = st.slider("Farm Size (kW)", min_value=10, max_value=10000, value=500, step=10)
with ec2:
    electricity_rate = st.slider("Electricity Rate (₹/kWh)", min_value=3, max_value=12, value=7)
with ec3:
    diesel_rate = st.slider("Diesel Price (₹/L)", min_value=80, max_value=120, value=95)

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
st.caption(f"Based on today's {daily_hours} productive solar hours in this location × {farm_size}kW farm × ₹{electricity_rate}/kWh rate")

# --- 7-DAY FORECAST + AI PLAN ---
st.divider()
st.subheader("📅 7-Day Solar Forecast + AI Plan")

@st.cache_data(ttl=3600)
def get_7day(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weathercode,shortwave_radiation_sum,precipitation_sum,windspeed_10m_max&forecast_days=7&timezone=auto"
    r = requests.get(url)
    return r.json()

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

    if wc >= 95:
        ai_plan = "🛡️ Shield closed all day"; recommendation = "🔴 Storm — protect panels"
    elif wc >= 61 or prec > 2:
        ai_plan = "🛡️ Shield closed — rain"; recommendation = "🟠 Rain — minimal harvest"
    elif est_output > 3000:
        ai_plan = "⚡ Full harvest + H₂ store"; recommendation = "🟢 Excellent day — max production"
    elif est_output > 1000:
        ai_plan = "🔋 Normal harvest + store"; recommendation = "🟡 Good day — normal ops"
    else:
        ai_plan = "🌙 Distribute stored energy"; recommendation = "⚪ Low solar — use reserves"

    day_rows.append({"Date": date, "Est. Output (Wh/m²)": est_output, "Rain (mm)": prec,
                     "Max Wind (km/h)": wind_max, "AI Plan": ai_plan, "Status": recommendation})

day_df = pd.DataFrame(day_rows)
st.dataframe(day_df, use_container_width=True, hide_index=True)

best_day = day_df.loc[day_df["Est. Output (Wh/m²)"].idxmax(), "Date"]
worst_day = day_df.loc[day_df["Est. Output (Wh/m²)"].idxmin(), "Date"]
storm_days = day_df[day_df["Rain (mm)"] > 2].shape[0]
st.info(f"🤖 **AI Weekly Insight:** Best production day → **{best_day}** | Storm/rain days → **{storm_days}** | Low output day → **{worst_day}** — pre-charge batteries before this date.")

# --- ALERT SYSTEM ---
st.divider()
st.subheader("🚨 Real-Time Alert System")

alerts = []
if wcode >= 95:
    alerts.append(("CRITICAL", "⛈️ THUNDERSTORM DETECTED", f"Immediate shield closure triggered. Location: {city_name}"))
if wcode >= 61 or rain > 0.5:
    alerts.append(("HIGH", "🌧️ HEAVY RAINFALL", f"Rain: {rain}mm. Shield closed. Panels protected."))
if wind > 60:
    alerts.append(("HIGH", "💨 EXTREME WIND", f"Wind: {wind} km/h — shield closed."))
if wind > 40:
    alerts.append(("MEDIUM", "⚠️ HIGH WIND WARNING", f"Wind: {wind} km/h — shield on standby."))
if solar_output < 10 and 7 < datetime.now().hour < 17:
    alerts.append(("MEDIUM", "☁️ LOW SOLAR OUTPUT", f"Only {solar_output} W/m² during daylight. Possible cloud cover."))
if sim_event == "bird":
    alerts.append(("HIGH", "🐦 BIRD ACTIVITY DETECTED", "Camera triggered — deterrent active. Shield partially closing."))
if sim_event == "dust":
    alerts.append(("HIGH", "🌫️ DUST STORM DETECTED", "Dust critical — 25% efficiency drop. Auto-clean sequence initiated."))
for row in day_rows:
    if "Storm" in row["Status"] or "Rain" in row["Status"]:
        alerts.append(("LOW", f"📅 UPCOMING: {row['Date']}", f"{row['AI Plan']} — Pre-charge batteries recommended."))

if not alerts:
    st.success("✅ All systems normal — No active alerts")
else:
    for level, title, msg in alerts:
        if level == "CRITICAL":
            st.error(f"🔴 **{title}**\n\n{msg}")
        elif level == "HIGH":
            st.error(f"🟠 **{title}**\n\n{msg}")
        elif level == "MEDIUM":
            st.warning(f"🟡 **{title}**\n\n{msg}")
        else:
            st.info(f"🔵 **{title}**\n\n{msg}")

st.caption(f"Alert engine last checked: {datetime.now().strftime('%H:%M:%S')} | Location: {city_name}")

# Auto refresh when auto sim is on
if auto_sim:
    time.sleep(5)
    st.rerun()

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

st.info(f"🤖 Without Solar OS: **{solar_output} W/m²** | With Solar OS protection: **{protected_output} W/m²** | Recovery: **{round(total_loss/max(protected_output,1)*100,1)}%**")

# --- GEOPOLITICAL IMPACT PANEL ---
st.divider()
st.subheader("🌍 Geopolitical Energy Independence")
st.caption("Why this matters beyond just electricity bills")

g1, g2 = st.columns(2)

with g1:
    st.markdown("""
    ### 🛢️ Current Reality
    - **20%** of world oil passes through Strait of Hormuz
    - **1 conflict** → global fuel prices spike
    - India imports **96%** of its crude oil
    - Every ₹1 rise in oil = **₹800Cr** extra import bill
    - Bangladesh, Philippines, Sri Lanka — economies collapse on fuel shock
    """)

with g2:
    st.markdown("""
    ### ☀️ Solar OS Reality
    - Sun sends Earth energy every hour = **1 year** of humanity's need
    - We capture **< 1%** of it
    - Solar OS maximizes what we DO capture
    - Every optimized farm = less oil dependency
    - **Energy sovereignty** — your own remote control
    """)

oil_saved = round(diesel_displaced_litres / 1000, 1)
st.success(f"🌍 This {farm_size}kW farm managed by Solar OS saves **{oil_saved} thousand litres** of oil/year — direct geopolitical independence.")

# --- WHY SOLAR OS EXPLAINER ---
st.divider()
st.subheader("🚀 Why Solar OS Exists")

w1, w2, w3 = st.columns(3)

with w1:
    st.error("""
    ### ❌ Problem Today
    Solar farms are **dumb**
    
    - Panels just sit there
    - No unified brain
    - Separate vendors for everything
    - Human monitors needed 24/7
    - Threats damage panels daily
    - Unpredictable output → grid rejects solar
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
    
    - Sense all threats in real-time
    - Decide autonomously
    - Protect, clean, convert, store
    - Predict & plan 7 days ahead
    - Tell grid exactly what's coming
    - Minimal human intervention
    """)

# --- FOSSIL vs SOLAR COMPARISON ---
st.divider()
st.subheader("⚖️ Solar OS vs Fossil Fuel — Real Comparison")

years = list(range(1, 26))
fossil_cost = [farm_size * 0.12 * 8760 * y for y in years]
solar_cost_cumulative = [farm_size * 500 + (farm_size * 0.02 * 8760 * y) for y in years]

comp_df = pd.DataFrame({
    "Year": years,
    "Fossil Fuel Cost (₹)": fossil_cost,
    "Solar OS Cost (₹)": solar_cost_cumulative
})

st.line_chart(comp_df.set_index("Year"))
breakeven = next((y for y, f, s in zip(years, fossil_cost, solar_cost_cumulative) if s < f), None)
if breakeven:
    st.success(f"💰 Solar OS breaks even at **Year {breakeven}** — after that it's pure savings for {25-breakeven} years.")
st.caption("Based on ₹12/kWh fossil cost vs ₹500/kW solar installation + ₹2/kWh maintenance")