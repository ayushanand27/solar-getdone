import streamlit as st

st.set_page_config(page_title="Solar OS", layout="wide", page_icon="☀️")

import pandas as pd

from utils.app_state import setup_app
from utils.maintenance_ai import (
    build_calendar,
    build_predictions,
    dry_streak_days,
    maintenance_costs,
    overall_health_score,
    subsystem_scores,
)

ctx = setup_app()

st.title("🔧 Predictive Maintenance AI")
st.caption("ML-based failure prediction and maintenance scheduling")

scores = subsystem_scores(ctx)
overall = overall_health_score(scores)
battery_level = min(100, int(ctx["solar_output"] / 2))
dry_days = dry_streak_days(ctx)

for name, score in scores.items():
    if score < 40:
        st.error(f"🚨 Immediate maintenance required: **{name}** (score {score}/100)")

st.subheader("🏥 Overall Maintenance Health")
h1, h2 = st.columns([1, 3])
with h1:
    grade = "🟢 Healthy" if overall >= 80 else "🟡 Monitor" if overall >= 60 else "🔴 Critical"
    st.metric("Maintenance Health Score", f"{overall}/100", grade)
with h2:
    st.progress(overall / 100)

st.divider()
st.subheader("⚙️ Subsystem Health")

s1, s2, s3, s4 = st.columns(4)
subsystem_cols = [s1, s2, s3, s4]
subsystem_details = {
    "Panel Health": (
        f"Dust streak: {dry_days} dry days · Temp: {ctx['temp']}°C · Wind: {ctx['wind']} km/h"
    ),
    "Inverter Health": (
        f"Operating hours est.: {sum(1 for r in ctx['radiation'] if r > 100)}h · "
        f"Temp stress: {'High' if ctx['temp'] > 38 else 'Normal'}"
    ),
    "Battery Health": (
        f"Charge level: {battery_level}% · Temp: {ctx['temp']}°C"
    ),
    "Structural Health": (
        f"Wind: {ctx['wind']} km/h · Storm days (7d forecast): "
        f"{sum(1 for c in ctx.get('forecast', {}).get('daily', {}).get('weathercode', []) if c >= 95)}"
    ),
}

for col, (name, score) in zip(subsystem_cols, scores.items()):
    with col:
        color = "#00C896" if score >= 80 else "#F7B731" if score >= 60 else "#EF4444"
        st.markdown(
            f"""
<div style="background:#161B22;border:1px solid #21262D;border-radius:10px;
padding:16px;border-top:3px solid {color};">
<div style="color:#8B949E;font-size:12px;">{name}</div>
<div style="color:{color};font-size:32px;font-weight:bold;">{score}/100</div>
<div style="color:#8B949E;font-size:11px;margin-top:8px;">{subsystem_details[name]}</div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.progress(score / 100)

st.divider()
st.subheader("🔮 Maintenance Predictions")

predictions = build_predictions(ctx, scores)
if predictions:
    pred_df = pd.DataFrame(predictions)
    st.dataframe(pred_df, use_container_width=True, hide_index=True)
else:
    st.success("No elevated maintenance risks detected for the next 60 days.")

st.divider()
st.subheader("📅 Maintenance Calendar (Next 30 Days)")

calendar_df = build_calendar(predictions)

def style_calendar(row):
    priority = row["Priority"]
    if "🔴" in priority:
        color = "background-color: #2A1010"
    elif "🟡" in priority:
        color = "background-color: #2A2208"
    else:
        color = "background-color: #0D2818" if row["Task"] != "—" else ""
    return [color] * len(row)

styled = calendar_df.style.apply(style_calendar, axis=1)
st.dataframe(styled, use_container_width=True, hide_index=True)

st.divider()
st.subheader("💰 Cost Savings — Predictive vs Reactive")

reactive_cost, predictive_cost, savings = maintenance_costs(overall)
c1, c2, c3 = st.columns(3)
c1.metric("Reactive Maintenance Cost", f"₹{reactive_cost:,}/year")
c2.metric("Predictive Maintenance Cost", f"₹{predictive_cost:,}/year")
c3.metric("Solar OS Saves", f"₹{savings:,}/year per farm")

st.caption(
    f"Estimates based on farm output {ctx['solar_output']} W/m², "
    f"location {ctx['city_name']}, and current subsystem health scores."
)
