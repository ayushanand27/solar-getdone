import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

st.set_page_config(page_title="Solar OS", layout="wide", page_icon="☀️")

# --- LOCATION SEARCH (must be before title) ---
st.sidebar.title("📍 Location")
city = st.sidebar.text_input("Enter City", value="Jaipur")

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
def ai_decision(wcode, wind, rain, radiation):
    solar_output = round(radiation[datetime.now().hour] * 0.22, 1)

    if wcode >= 95:
        status = "🛡️ SHIELD CLOSED"
        action = "Thunderstorm detected — panels protected"
        mode = "protection"
        shield = "CLOSED"
        shield_reason = "Thunderstorm detected"
        threat_level = "CRITICAL"
    elif wcode >= 61 or rain > 0.5:
        status = "🛡️ SHIELD CLOSED"
        action = "Heavy rain — panels protected"
        mode = "protection"
        shield = "CLOSED"
        shield_reason = "Heavy rainfall detected"
        threat_level = "HIGH"
    elif wind > 60:
        status = "🛡️ SHIELD CLOSED"
        action = "Extreme wind — panels protected"
        mode = "protection"
        shield = "CLOSED"
        shield_reason = "Extreme wind speed"
        threat_level = "HIGH"
    elif wind > 40:
        status = "⚠️ MONITORING"
        action = "High wind — monitoring closely"
        mode = "monitor"
        shield = "READY"
        shield_reason = "Wind speed elevated — shield on standby"
        threat_level = "MEDIUM"
    elif solar_output > 150:
        status = "⚡ FULL CONVERSION"
        action = "Peak sunlight — maximum energy harvesting"
        mode = "harvest"
        shield = "OPEN"
        shield_reason = "Clear sky — full exposure"
        threat_level = "LOW"
    elif solar_output > 50:
        status = "🔋 STORING + H₂"
        action = "Moderate sunlight — storing battery + making hydrogen"
        mode = "store"
        shield = "OPEN"
        shield_reason = "Normal conditions"
        threat_level = "LOW"
    else:
        status = "🌙 DISTRIBUTING"
        action = "Low/no sunlight — distributing stored energy"
        mode = "distribute"
        shield = "OPEN"
        shield_reason = "No threat detected"
        threat_level = "LOW"

    return status, action, mode, solar_output, shield, shield_reason, threat_level

status, action, mode, solar_output, shield, shield_reason, threat_level = ai_decision(wcode, wind, rain, radiation)

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
elif mode == "monitor":
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
        st.error(f"""
        ### 🔒 SHIELD: CLOSED
        **Reason:** {shield_reason}
        
        Panels are fully protected.
        No energy harvesting active.
        """)
    elif shield == "READY":
        st.warning(f"""
        ### ⚠️ SHIELD: STANDBY
        **Reason:** {shield_reason}
        
        Shield ready to deploy instantly.
        Partial harvesting active.
        """)
    else:
        st.success(f"""
        ### ✅ SHIELD: OPEN
        **Reason:** {shield_reason}
        
        Panels fully exposed.
        Maximum harvesting active.
        """)

with s2:
    st.markdown("### 🎯 Threat Assessment")
    if threat_level == "CRITICAL":
        st.error("🔴 CRITICAL THREAT")
        st.progress(100)
    elif threat_level == "HIGH":
        st.error("🟠 HIGH THREAT")
        st.progress(75)
    elif threat_level == "MEDIUM":
        st.warning("🟡 MEDIUM THREAT")
        st.progress(50)
    else:
        st.success("🟢 LOW THREAT")
        st.progress(15)
    st.caption(f"Weather code: {wcode} | Wind: {wind} km/h | Rain: {rain}mm")

with s3:
    st.markdown("### 📋 Threat Breakdown")
    threats = {
        "⛈️ Thunderstorm": "🔴 YES" if wcode >= 95 else "🟢 NO",
        "🌧️ Heavy Rain": "🔴 YES" if rain > 0.5 else "🟢 NO",
        "💨 Extreme Wind": "🔴 YES" if wind > 60 else "🟢 NO",
        "⚠️ High Wind": "🟡 WATCH" if 40 < wind <= 60 else "🟢 NO",
        "🌫️ Dust Storm": "🟢 NO",
        "🐦 Bird Activity": "🟢 NO",
    }
    for threat, val in threats.items():
        st.markdown(f"{threat} — **{val}**")

st.divider()

# --- SOLAR RADIATION CHART ---
st.subheader("☀️ Today's Solar Radiation Forecast")
df = pd.DataFrame({"Time": hours, "Radiation (W/m²)": radiation})
df["Estimated Output (W/m²)"] = df["Radiation (W/m²)"] * 0.22
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
    if hour_output > 150:
        decision = "⚡ Full Conversion"
        sh = "🟢 Open"
    elif hour_output > 50:
        decision = "🔋 Store + H₂"
        sh = "🟢 Open"
    else:
        decision = "🌙 Distribute"
        sh = "🟢 Open"
    log_rows.append({
        "Hour": h[11:16],
        "Solar Output (W/m²)": hour_output,
        "AI Decision": decision,
        "Shield": sh
    })

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
        ai_plan = "🛡️ Shield closed all day"
        recommendation = "🔴 Storm — protect panels"
    elif wc >= 61 or prec > 2:
        ai_plan = "🛡️ Shield closed — rain"
        recommendation = "🟠 Rain — minimal harvest"
    elif est_output > 3000:
        ai_plan = "⚡ Full harvest + H₂ store"
        recommendation = "🟢 Excellent day — max production"
    elif est_output > 1000:
        ai_plan = "🔋 Normal harvest + store"
        recommendation = "🟡 Good day — normal ops"
    else:
        ai_plan = "🌙 Distribute stored energy"
        recommendation = "⚪ Low solar — use reserves"

    day_rows.append({
        "Date": date,
        "Est. Output (Wh/m²)": est_output,
        "Rain (mm)": prec,
        "Max Wind (km/h)": wind_max,
        "AI Plan": ai_plan,
        "Status": recommendation
    })

day_df = pd.DataFrame(day_rows)
st.dataframe(day_df, use_container_width=True, hide_index=True)

# AI insight
best_day = day_df.loc[day_df["Est. Output (Wh/m²)"].idxmax(), "Date"]
worst_day = day_df.loc[day_df["Est. Output (Wh/m²)"].idxmin(), "Date"]
storm_days = day_df[day_df["Rain (mm)"] > 2].shape[0]

st.info(f"🤖 **AI Weekly Insight:** Best production day → **{best_day}** | Storm/rain days → **{storm_days}** | Low output day → **{worst_day}** — pre-charge batteries before this date.")

# --- ALERT SYSTEM ---
st.divider()
st.subheader("🚨 Real-Time Alert System")

alerts = []

if wcode >= 95:
    alerts.append(("CRITICAL", "⛈️ THUNDERSTORM DETECTED", f"Immediate shield closure triggered. All harvesting stopped. Location: {city_name}"))
if wcode >= 61 or rain > 0.5:
    alerts.append(("HIGH", "🌧️ HEAVY RAINFALL", f"Rain: {rain}mm detected. Shield closed. Panels protected."))
if wind > 60:
    alerts.append(("HIGH", "💨 EXTREME WIND", f"Wind: {wind} km/h — exceeds safe limit. Shield closed."))
if wind > 40:
    alerts.append(("MEDIUM", "⚠️ HIGH WIND WARNING", f"Wind: {wind} km/h — shield on standby."))
if solar_output < 10 and datetime.now().hour > 7 and datetime.now().hour < 17:
    alerts.append(("MEDIUM", "☁️ LOW SOLAR OUTPUT", f"Only {solar_output} W/m² during daylight hours. Possible cloud cover."))


# 7-day storm warning
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