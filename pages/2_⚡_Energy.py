import streamlit as st
st.set_page_config(page_title="Solar OS", layout="wide", page_icon="☀️")

import altair as alt
import pandas as pd

from utils.app_state import setup_app

ctx = setup_app()

st.title("⚡ Energy Management")
st.caption(f"Storage, hydrogen, and hourly AI decisions | 📍 {ctx['city_name']}")

if ctx["shield"] == "CLOSED" or ctx["mode"] == "protection":
    st.error(
        f"🛡️ **Protection mode active** — Shield {ctx['shield']}. "
        f"Energy harvesting paused: {ctx['action']}"
    )
elif ctx["mode"] == "monitor" and ctx.get("sim_event") in ("bird", "dust"):
    st.warning(f"⚠️ **Monitoring mode** — {ctx['status']}: {ctx['action']}")

st.subheader("☀️ Today's Solar Radiation Forecast")
df = pd.DataFrame(
    {
        "Hour": [t[11:16] for t in ctx["hours"]],
        "Radiation (W/m²)": [float(r or 0) for r in ctx["radiation"]],
    }
)
df["Estimated Output (W/m²)"] = (df["Radiation (W/m²)"] * 0.22).round(1)
if ctx["sim_event"] == "dust":
    df["Estimated Output (W/m²)"] = (df["Estimated Output (W/m²)"] * 0.75).round(1)
    st.caption("⚠️ Dust storm active — showing 25% efficiency loss")
hour_order = df["Hour"].tolist()
radiation_chart = (
    alt.Chart(df)
    .mark_line(point=True, color="#F7B731")
    .encode(
        x=alt.X("Hour:N", sort=hour_order, title="Hour"),
        y=alt.Y("Estimated Output (W/m²):Q", title="Estimated Output (W/m²)", scale=alt.Scale(zero=True)),
        tooltip=["Hour", "Radiation (W/m²)", "Estimated Output (W/m²)"],
    )
    .properties(height=280)
)
st.altair_chart(radiation_chart, use_container_width=True)

st.subheader("🧪 Hydrogen Storage Simulation")
h2_stored = ctx.get("h2_kg", st.session_state.get("h2_kg", round(sum(r * 0.22 * 0.7 for r in ctx["radiation"] if r > 100) / 1000, 2)))
st.metric("Estimated H₂ Generated Today", f"{h2_stored} kg")
st.caption("Based on today's radiation forecast × panel efficiency × electrolysis efficiency")
st.divider()
st.caption("🔄 Data refreshes every 5 minutes automatically")

st.subheader("🔋 Energy Storage System")
b1, b2, b3 = st.columns(3)
battery_level = ctx.get("battery_level", st.session_state.get("battery_level", min(100, int(ctx["solar_output"] / 2))))
h2_level = ctx.get("h2_level", st.session_state.get("h2_level", min(100, int(h2_stored * 40))))

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
    st.caption(f"Battery: {battery_level}% | H₂: {h2_level}% | Solar: {ctx['solar_output']} W/m²")

st.divider()
st.subheader("🤖 24hr AI Decision Log")
log_rows = []
for h, r in zip(ctx["hours"], ctx["radiation"]):
    hour_output = round(r * 0.22 * (0.75 if ctx["sim_event"] == "dust" else 1), 1)
    if ctx["shield"] == "CLOSED" or ctx["mode"] == "protection":
        decision, sh = "🛡️ Protection", "🔒 Closed"
    elif hour_output > 150:
        decision, sh = "⚡ Full Conversion", "🟢 Open"
    elif hour_output > 50:
        decision, sh = "🔋 Store + H₂", "🟢 Open"
    else:
        decision, sh = "🌙 Distribute", "🟢 Open"
    if ctx["sim_event"] == "bird":
        sh = "⚠️ Partial"
    log_rows.append({"Hour": h[11:16], "Solar Output (W/m²)": hour_output, "AI Decision": decision, "Shield": sh})
st.dataframe(pd.DataFrame(log_rows), use_container_width=True, hide_index=True)
