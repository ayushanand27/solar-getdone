import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

st.set_page_config(page_title="Solar OS", layout="wide", page_icon="☀️")

st.title("☀️ Solar OS — Autonomous Solar Farm Intelligence")
st.caption("Real-time AI decision engine for solar farm management")

lat, lon = 26.9124, 75.7873

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
        status = "⚡ FULL CONVERSION"
        action = "Peak sunlight — maximum energy harvesting"
        mode = "harvest"
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

# Shield visual status
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

# Threat level
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

# Threat breakdown
with s3:
    st.markdown("### 📋 Threat Breakdown")
    threats = {
        "⛈️ Thunderstorm": "🔴 YES" if wcode >= 95 else "🟢 NO",
        "🌧️ Heavy Rain": "🔴 YES" if rain > 0.5 else "🟢 NO",
        "💨 Extreme Wind": "🔴 YES" if wind > 60 else "🟢 NO",
        "⚠️ High Wind": "🟡 WATCH" if 40 < wind <= 60 else "🟢 NO",
        "🌫️ Dust Storm": "🟢 NO",  # sensor se aayega future mein
        "🐦 Bird Activity": "🟢 NO",  # camera se aayega future mein
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

# --- AUTO REFRESH ---
st.divider()
st.caption("🔄 Data refreshes every 5 minutes automatically")
time.sleep(0)

# --- BATTERY + H2 STORAGE ---
st.divider()
st.subheader("🔋 Energy Storage System")

b1, b2, b3 = st.columns(3)

# Simulate battery level based on solar output
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
        decision = "→ Redirecting to H₂ conversion"
        st.warning(decision)
    elif battery_level < 30:
        decision = "→ Priority: Charge battery first"
        st.error(decision)
    elif h2_level > 80 and battery_level > 80:
        decision = "→ Both full: Export to grid"
        st.success(decision)
    else:
        decision = "→ Normal: Battery + H₂ parallel"
        st.success(decision)
    
    st.caption(f"Battery: {battery_level}% | H₂: {h2_level}% | Solar: {solar_output} W/m²")

    # --- 24HR AI DECISION LOG ---
st.divider()
st.subheader("🤖 24hr AI Decision Log")

log_rows = []
for i, (h, r) in enumerate(zip(hours, radiation)):
    hour_output = round(r * 0.22, 1)
    if hour_output > 150:
        decision = "⚡ Full Conversion"
        shield = "🟢 Open"
    elif hour_output > 50:
        decision = "🔋 Store + H₂"
        shield = "🟢 Open"
    elif hour_output > 0:
        decision = "🌙 Distribute"
        shield = "🟢 Open"
    else:
        decision = "🌙 Distribute"
        shield = "🟢 Open"

    log_rows.append({
        "Hour": h[11:16],
        "Solar Output (W/m²)": hour_output,
        "AI Decision": decision,
        "Shield": shield
    })

log_df = pd.DataFrame(log_rows)
st.dataframe(log_df, use_container_width=True, hide_index=True)