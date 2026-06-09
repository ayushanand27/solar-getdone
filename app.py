import streamlit as st
st.set_page_config(page_title="Solar OS", layout="wide", page_icon="☀️")

from utils.app_state import render_edge_banner, setup_app
from utils.mqtt_client import publish_to_hivemq

ctx = setup_app()

success, msg = publish_to_hivemq(
    ctx["solar_output"],
    ctx["temp"],
    ctx["wind"],
    ctx["shield"],
    ctx["mode"],
    ctx["threat_level"],
)
try:
    mqtt_host = st.secrets["mqtt"]["host"]
except (KeyError, FileNotFoundError, AttributeError):
    mqtt_host = ""

st.session_state.mqtt_status = {
    "success": success,
    "message": msg,
    "host": mqtt_host,
}

st.title("☀️ Solar OS — Autonomous Solar Farm Intelligence")
st.caption(f"Real-time AI decision engine | 📍 {ctx['city_name']}")
if success:
    st.caption("📡 HiveMQ: ✅ Published to cloud")
else:
    st.caption(f"📡 HiveMQ: ❌ {msg}")
render_edge_banner(ctx)

col1, col2, col3, col4 = st.columns(4)
col1.metric("🌡️ Temperature", f"{ctx['temp']}°C")
col2.metric("💨 Wind Speed", f"{ctx['wind']} km/h")
col3.metric("🌧️ Precipitation", f"{ctx['rain']} mm")
col4.metric("☀️ Solar Output", f"{ctx['solar_output']} W/m²")
st.divider()

if ctx["mode"] == "protection":
    st.error(f"**{ctx['status']}** — {ctx['action']}")
elif ctx["mode"] == "harvest":
    st.success(f"**{ctx['status']}** — {ctx['action']}")
elif ctx["mode"] == "monitor":
    st.warning(f"**{ctx['status']}** — {ctx['action']}")
elif ctx["mode"] == "store":
    st.warning(f"**{ctx['status']}** — {ctx['action']}")
else:
    st.info(f"**{ctx['status']}** — {ctx['action']}")

st.divider()
st.markdown("Use the sidebar to navigate pages — **Shield**, **Energy**, **Forecast**, **Analytics**, and **Edge Node**.")
