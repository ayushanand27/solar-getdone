import streamlit as st
st.set_page_config(page_title="Solar OS", layout="wide", page_icon="☀️")

from utils.app_state import render_edge_banner, setup_app
from utils.health_score import calculate_health_score
from utils.mqtt_client import publish_if_due

ctx = setup_app()

success, msg = publish_if_due(
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
metric_cards = [
    (col1, "Temperature", f"{ctx['temp']}°C", "#EF4444"),
    (col2, "Wind Speed", f"{ctx['wind']} km/h", "#3B82F6"),
    (col3, "Precipitation", f"{ctx['rain']} mm", "#8B5CF6"),
    (col4, "Solar Output", f"{ctx['solar_output']} W/m²", "#F7B731"),
]
for col, label, value, color in metric_cards:
    with col:
        st.markdown(
            f"""
<div style="background:#161B22; border:1px solid #21262D;
border-radius:8px; padding:16px; text-align:center;
border-top: 3px solid {color};">
<div style="color:#8B949E; font-size:12px;">{label}</div>
<div style="color:{color}; font-size:28px; font-weight:bold;">
{value}</div>
</div>
""",
            unsafe_allow_html=True,
        )

h2_kg = round(sum(r * 0.22 * 0.7 for r in ctx["radiation"] if r > 100) / 1000, 2)
battery = min(100, int(ctx["solar_output"] / 2))
h2_level = min(100, int(h2_kg * 40))
health_score, health_grade = calculate_health_score(
    ctx["solar_output"],
    ctx["threat_level"],
    battery,
    h2_level,
    ctx["shield"],
    ctx["wind"],
    ctx["rain"],
    ctx["wcode"],
)
if health_score >= 80:
    health_color = "#00C896"
elif health_score >= 60:
    health_color = "#F7B731"
else:
    health_color = "#EF4444"

st.markdown(
    f"""
<div style="background:#161B22; border:1px solid #21262D; border-radius:12px;
padding:24px; margin-top:16px; text-align:center;
border-top: 4px solid {health_color};">
<div style="color:#8B949E; font-size:14px; margin-bottom:8px;">
🏥 Farm Health Score</div>
<div style="color:{health_color}; font-size:48px; font-weight:bold; line-height:1.1;">
{health_score}<span style="font-size:24px; color:#8B949E;">/100</span></div>
<div style="color:{health_color}; font-size:16px; font-weight:600; margin:10px 0 16px;">
{health_grade}</div>
<div style="background:#21262D; border-radius:999px; height:12px; overflow:hidden;">
<div style="background:{health_color}; width:{health_score}%; height:12px; border-radius:999px;"></div>
</div>
</div>
""",
    unsafe_allow_html=True,
)
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

mqtt_label = "✅ Live" if success else "❌ Offline"
q1, q2, q3 = st.columns(3)
quick_stats = [
    (q1, "H₂ Today", f"{h2_kg} kg", "#00C896"),
    (q2, "Battery", f"{battery}%", "#3B82F6"),
    (q3, "MQTT", mqtt_label, "#F7B731" if success else "#EF4444"),
]
for col, label, value, color in quick_stats:
    with col:
        st.markdown(
            f"""
<div style="background:#161B22; border:1px solid #21262D;
border-radius:8px; padding:12px; text-align:center;
border-left: 3px solid {color};">
<div style="color:#8B949E; font-size:11px;">{label}</div>
<div style="color:{color}; font-size:20px; font-weight:bold; margin-top:4px;">
{value}</div>
</div>
""",
            unsafe_allow_html=True,
        )

st.divider()
st.markdown("Use the sidebar to navigate pages — **Shield**, **Energy**, **Forecast**, **Analytics**, and **Edge Node**.")
