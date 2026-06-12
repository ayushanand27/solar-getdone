import streamlit as st
st.set_page_config(page_title="Solar OS", layout="wide", page_icon="☀️")

import time

import pandas as pd

from utils.app_state import render_edge_banner, setup_app
from utils.mqtt_client import publish_to_hivemq
from utils.mobile_alerts import (
    SNS_TOPIC_ARN,
    append_alert,
    init_alert_state,
    latest_phone_message,
    process_auto_alerts,
    render_alert_config,
    sns_estimated_cost,
)
from utils.email_alerts import send_email_alert
from utils.mqtt_sim import publish_mqtt_messages

ctx = setup_app()
init_alert_state()

if "mqtt_status" not in st.session_state or not st.session_state.get("mqtt_status", {}).get("success"):
    success, msg = publish_to_hivemq(
        ctx.get("solar_output", 0),
        ctx.get("temp", 30),
        ctx.get("wind", 10),
        ctx.get("shield", "OPEN"),
        ctx.get("mode", "distribute"),
        ctx.get("threat_level", "LOW"),
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

st.title("🖥️ Edge Node")
st.caption(f"Local inference monitor — RPi4-ARM64 | 📍 {ctx['city_name']}")
render_edge_banner(ctx)

st.subheader("🖥️ Edge Node Monitor")
edge_uptime_s = int(time.time() - st.session_state.edge_start_time)
edge_uptime_m, edge_uptime_s_rem = divmod(edge_uptime_s, 60)
edge_uptime_str = f"{edge_uptime_m}m {edge_uptime_s_rem}s" if edge_uptime_m else f"{edge_uptime_s}s"

e1, e2, e3, e4 = st.columns(4)
with e1:
    st.metric("Inference Latency", f"{ctx['edge_latency']} ms" if ctx["edge_mode"] else "—")
with e2:
    st.metric("CPU Usage", f"{ctx['edge_cpu']}%" if ctx["edge_mode"] else "—")
with e3:
    st.metric(
        "Memory",
        f"{ctx['edge_memory_used']} / {ctx['edge_memory_total']} MB" if ctx["edge_mode"] else "—",
    )
with e4:
    st.metric("Uptime", edge_uptime_str)

if ctx["edge_mode"]:
    st.caption(f"CPU load on RPi4-ARM64 — {ctx['edge_cpu']}%")
    st.progress(ctx["edge_cpu"] / 100)
else:
    st.caption("Edge Mode off — metrics available when running locally on RPi4-ARM64.")
    st.progress(0)

st.markdown("#### 📜 Recent Edge Decisions")
if ctx["edge_mode"] and st.session_state.edge_decision_log:
    for row in reversed(st.session_state.edge_decision_log):
        st.markdown(f"`{row['time']}` — **{row['decision']}** ({row['latency_ms']} ms)")
else:
    st.caption("No edge decisions logged yet. Enable **🖥️ Edge Mode** to stream local inference decisions.")

st.divider()
st.subheader("📡 MQTT Feed")
broker_label = publish_mqtt_messages(ctx)
st.caption(f"Broker: **{broker_label}** — publishes 4 topics on every refresh")

aws_col1, aws_col2 = st.columns([2, 1])
mqtt_status = st.session_state.get(
    "mqtt_status",
    {"success": False, "message": "Visit Home page to publish", "host": ""},
)
mqtt_host = mqtt_status.get("host", "")
if not mqtt_host:
    try:
        mqtt_host = st.secrets["mqtt"]["host"]
    except (KeyError, FileNotFoundError, AttributeError):
        mqtt_host = "—"

with aws_col1:
    if mqtt_status.get("success"):
        st.success(f"📡 HiveMQ Cloud: ✅ Live — `{mqtt_host}`")
    else:
        st.error(f"📡 HiveMQ Cloud: ❌ {mqtt_status.get('message', 'Not connected')}")
with aws_col2:
    last_sync = st.session_state.get("mqtt_last_sync", "—")
    st.metric("Last MQTT Sync", last_sync)

st.markdown("#### Live MQTT Message Feed")
feed = list(reversed(st.session_state.get("mqtt_feed", [])))
if feed:
    st.dataframe(pd.DataFrame(feed), use_container_width=True, hide_index=True)
else:
    st.info("MQTT messages will appear here after the first refresh.")

st.divider()
st.subheader("📱 Mobile Alert System (AWS SNS Mock)")

if "alert_email" not in st.session_state:
    try:
        st.session_state.alert_email = st.secrets["email"]["recipient"]
    except (KeyError, FileNotFoundError, AttributeError):
        st.session_state.alert_email = ""

email_col1, email_col2 = st.columns([2, 1])
with email_col1:
    st.session_state.alert_email = st.text_input(
        "📧 Alert Email",
        value=st.session_state.alert_email,
        key="alert_email_input",
    )
with email_col2:
    st.checkbox("☑ Send email alerts (SMTP)", key="alert_email_enabled")

alert_config = render_alert_config()
process_auto_alerts(ctx, alert_config)

if st.button("🔔 Test Alert", use_container_width=False):
    to_email = st.session_state.get("alert_email", "").strip()
    if not to_email:
        try:
            to_email = st.secrets["email"]["recipient"].strip()
        except (KeyError, FileNotFoundError, AttributeError, TypeError):
            to_email = ""

    if not to_email:
        st.error("No email configured")
    else:
        city = st.session_state.get("city_name", ctx["city_name"])
        test_message = (
            f"Test alert from Solar OS — {city} farm online and monitoring."
        )
        append_alert(
            "Test",
            test_message,
            channel="Push",
            status="📤 Sending",
            send_email=False,
        )

        if st.session_state.get("alert_email_enabled", True):
            success, msg = send_email_alert(
                "Test Alert",
                f"Solar OS is online and monitoring your farm at {city}. "
                f"All systems operational.",
                to_email,
            )
            if success:
                st.session_state.last_email_status = f"✅ Email sent to {to_email}"
                st.success(f"✅ Email sent to {to_email}")
            else:
                st.session_state.last_email_status = f"❌ Email failed: {msg}"
                st.error(f"❌ Email failed: {msg}")
        else:
            st.info("Email alerts disabled — toggle on to send")

if st.session_state.get("last_email_status"):
    status_msg = st.session_state.last_email_status
    if status_msg.startswith("✅"):
        st.success(status_msg)
    else:
        st.error(status_msg)

phone_msg = latest_phone_message(ctx)
st.markdown(
    f"""
<div style="max-width:320px;margin:16px auto;padding:12px;background:#111;border-radius:24px;
border:3px solid #333;box-shadow:0 8px 32px rgba(0,0,0,0.4);">
  <div style="background:#1a1a2e;border-radius:16px;padding:16px;color:#fff;font-family:sans-serif;">
    <div style="font-size:11px;color:#888;margin-bottom:8px;">Solar OS Alert 🌞 · now</div>
    <div style="font-size:14px;line-height:1.5;">
      ⚠️ {phone_msg}
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown("#### Alert Log")
alert_log = list(reversed(st.session_state.get("alert_log", [])))
if alert_log:
    st.dataframe(pd.DataFrame(alert_log), use_container_width=True, hide_index=True)
else:
    st.caption("No alerts sent yet. Enable alert types above or click **🔔 Test Alert**.")

sns_count = st.session_state.get("sns_messages_today", 0)
sns_cost = sns_estimated_cost(sns_count)
s1, s2, s3 = st.columns(3)
s1.markdown(f"**📡 SNS Topic:** `{SNS_TOPIC_ARN}`")
s2.metric("Messages Published Today", sns_count)
s3.metric("Estimated SNS Cost", f"${sns_cost:.7f}")
