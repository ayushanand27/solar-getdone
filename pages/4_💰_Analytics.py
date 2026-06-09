import streamlit as st
st.set_page_config(page_title="Solar OS", layout="wide", page_icon="☀️")

from datetime import datetime

import pandas as pd

from utils.app_state import setup_app
from utils.pdf_report import (
    build_forecast_rows,
    build_recommendations,
    compute_analytics_metrics,
    generate_farm_report,
)

ctx = setup_app()

st.title("💰 Analytics")
st.caption(f"Savings, efficiency, and long-term ROI | 📍 {ctx['city_name']}")

farm_size_report = st.session_state.get("analytics_farm_size", 500)
electricity_rate_report = st.session_state.get("analytics_electricity_rate", 7)
diesel_rate_report = st.session_state.get("analytics_diesel_rate", 95)
metrics_report = compute_analytics_metrics(
    ctx, farm_size_report, electricity_rate_report, diesel_rate_report
)
forecast_rows = build_forecast_rows(ctx)
recommendations = build_recommendations(ctx, metrics_report)
report_date = datetime.now().strftime("%Y-%m-%d")
report_time = datetime.now().strftime("%H:%M:%S")
city_slug = ctx["city_name"].replace(" ", "_")
pdf_bytes = generate_farm_report(
    ctx, metrics_report, forecast_rows, recommendations, report_date, report_time
)

st.download_button(
    label="📄 Download Farm Report",
    data=pdf_bytes,
    file_name=f"SolarOS_Report_{city_slug}_{report_date}.pdf",
    mime="application/pdf",
)

st.divider()
st.subheader("💰 Energy Savings Calculator")
st.caption("If Solar OS was managing a real farm here — what would be saved?")
ec1, ec2, ec3 = st.columns(3)
with ec1:
    farm_size = st.slider("Farm Size (kW)", 10, 10000, 500, 10, key="analytics_farm_size")
with ec2:
    electricity_rate = st.slider("Electricity Rate (₹/kWh)", 3, 12, 7, key="analytics_electricity_rate")
with ec3:
    diesel_rate = st.slider("Diesel Price (₹/L)", 80, 120, 95, key="analytics_diesel_rate")

daily_hours = sum(1 for r in ctx["radiation"] if r * 0.22 > 50)
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

st.divider()
st.subheader("📉 Efficiency Loss Tracker")
st.caption("Real cost of NOT having Solar OS")
el1, el2, el3, el4 = st.columns(4)
dust_loss = round(ctx["solar_output"] * 0.28, 1)
bird_loss = round(ctx["solar_output"] * 0.05, 1)
temp_loss = round(max(0, (ctx["temp"] - 25) * 0.004 * ctx["solar_output"]), 1)
total_loss = round(dust_loss + bird_loss + temp_loss, 1)
protected_output = round(ctx["solar_output"] + total_loss, 1)
el1.metric("🌫️ Dust Loss", f"{dust_loss} W/m²", "-28% typical")
el2.metric("🐦 Bird Loss", f"{bird_loss} W/m²", "-5% typical")
el3.metric("🌡️ Heat Loss", f"{temp_loss} W/m²", f"Temp: {ctx['temp']}°C")
el4.metric("💡 With Solar OS", f"{protected_output} W/m²", f"+{total_loss} recovered")
recovery_pct = round(total_loss / max(protected_output, 1) * 100, 1)
st.info(
    f"🤖 Without Solar OS: **{ctx['solar_output']} W/m²** | "
    f"With Solar OS: **{protected_output} W/m²** | Recovery: **{recovery_pct}%**"
)

st.divider()
st.subheader("⚖️ Solar OS vs Fossil Fuel — 25 Year Cost")
years = list(range(1, 26))
fossil_cost = [farm_size * 0.12 * 8760 * y for y in years]
solar_cost_cumulative = [farm_size * 500 + (farm_size * 0.02 * 8760 * y) for y in years]
comp_df = pd.DataFrame({"Year": years, "Fossil Fuel Cost (₹)": fossil_cost, "Solar OS Cost (₹)": solar_cost_cumulative})
st.line_chart(comp_df.set_index("Year"))
breakeven = next((y for y, f, s in zip(years, fossil_cost, solar_cost_cumulative) if s < f), None)
if breakeven:
    st.success(f"💰 Solar OS breaks even at **Year {breakeven}** — then **{25 - breakeven} years of pure savings.**")
st.caption("Based on ₹12/kWh fossil cost vs ₹500/kW solar installation + ₹2/kWh maintenance")

st.divider()
st.subheader("🌍 Geopolitical Energy Independence")
st.caption("Why this matters beyond electricity bills")
g1, g2 = st.columns(2)
with g1:
    st.markdown(
        """
### 🛢️ Current Reality
- **20%** of world oil passes through Strait of Hormuz
- **1 conflict** → global fuel prices spike instantly
- India imports **96%** of its crude oil
- Bangladesh, Philippines — economies collapse on fuel shock
- Solar exists but is **poorly managed** — massive waste
    """
    )
with g2:
    st.markdown(
        """
### ☀️ Solar OS Reality
- Sun sends enough energy in **1 hour** to power humanity for 1 year
- We capture **< 1%** of available solar energy
- Solar OS maximizes what we DO capture
- Every optimized farm = less oil dependency
- **Energy sovereignty** — your own remote control
    """
    )
oil_saved = round(diesel_displaced_litres / 1000, 1)
st.success(
    f"🌍 This {farm_size}kW farm managed by Solar OS saves **{oil_saved}K litres** "
    "of oil/year — direct geopolitical independence."
)

st.divider()
st.subheader("🚀 Why Solar OS Exists")
w1, w2, w3 = st.columns(3)
with w1:
    st.error(
        """
### ❌ Problem Today
Solar farms are **dumb**

- Panels just sit there
- No unified AI brain
- Separate vendors for everything
- Human monitors 24/7
- Threats damage panels daily
- Unpredictable → grid rejects solar
    """
    )
with w2:
    st.warning(
        """
### ⚙️ What Exists
Fragmented solutions

- Cleaning robots (separate)
- Weather APIs (separate)
- Battery management (separate)
- Grid software (separate)
- No system talks to another
- SpaceX model missing in solar
    """
    )
with w3:
    st.success(
        """
### ✅ Solar OS Vision
One AI brain for everything

- Sense all threats real-time
- Decide autonomously
- Protect, clean, convert, store
- Predict & plan 7 days ahead
- Tell grid exactly what's coming
- Minimal human intervention
    """
    )
