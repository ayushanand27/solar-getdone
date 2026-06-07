import streamlit as st
st.set_page_config(page_title="Solar OS", layout="wide", page_icon="☀️")

import time

import pandas as pd

from utils.app_state import render_edge_banner, setup_app
from utils.mqtt_sim import publish_mqtt_messages

ctx = setup_app()

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
with aws_col1:
    st.success("✅ Synced to AWS IoT Greengrass")
with aws_col2:
    last_sync = st.session_state.get("mqtt_last_sync", "—")
    st.metric("Last AWS Sync", last_sync)

st.markdown("#### Live MQTT Message Feed")
feed = list(reversed(st.session_state.get("mqtt_feed", [])))
if feed:
    st.dataframe(pd.DataFrame(feed), use_container_width=True, hide_index=True)
else:
    st.info("MQTT messages will appear here after the first refresh.")
