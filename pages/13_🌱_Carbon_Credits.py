import streamlit as st

st.set_page_config(page_title="Solar OS", layout="wide", page_icon="☀️")

from datetime import datetime

import altair as alt
import pandas as pd

from utils.app_state import setup_app
from utils.carbon_credits import (
    build_comparison_table,
    build_projection,
    calculate_esg,
    calculate_metrics,
    derive_daily_hours,
    generate_esg_pdf,
    governance_score,
)

ctx = setup_app()
report_date = datetime.now().strftime("%Y-%m-%d")

st.title("🌱 Carbon Credits & ESG Dashboard")
st.caption("Monetize your clean energy — India Carbon Credit Market 2026")

st.info(
    "India launched its Carbon Credit Trading Scheme (CCTS) in 2023. "
    "Solar farms generating clean energy can earn carbon credits tradeable on the "
    "Indian Carbon Market (ICM). 1 Carbon Credit = 1 tonne CO₂ avoided."
)

default_farm_size = max(10, min(50000, int(ctx.get("solar_output", 500) * 3)))
derived_hours = derive_daily_hours(ctx)

st.subheader("🧮 Carbon Generation Calculator")
c1, c2, c3 = st.columns(3)
with c1:
    farm_size_kw = st.slider("Farm size (kW)", 10, 50000, default_farm_size, step=10)
with c2:
    years_op = st.slider("Years of operation", 1, 25, 25)
with c3:
    emission_factor = st.slider(
        "Grid emission factor (kg CO₂/kWh)",
        0.40,
        1.20,
        0.71,
        step=0.01,
        help="India grid default: 0.71 kg CO₂/kWh",
    )

st.caption(
    f"Live farm data: 📍 {ctx['city_name']} · "
    f"Est. productive hours today: **{derived_hours:.1f}h** · "
    f"Solar output: **{ctx['solar_output']} W/m²**"
)

metrics = calculate_metrics(farm_size_kw, years_op, emission_factor, ctx)
governance = governance_score(st.session_state)
esg = calculate_esg(metrics, ctx, governance)
projection_df = build_projection(metrics, projection_years=25)
comparison_df = build_comparison_table(farm_size_kw, metrics)

st.divider()
st.subheader("💰 Revenue Breakdown")
r1, r2, r3, r4 = st.columns(4)
r1.metric("Annual CO₂ Avoided", f"{metrics['co2_avoided_tonnes']:,.1f} tonnes")
r2.metric("Annual Credits Generated", f"{metrics['carbon_credits']:,.1f} credits")
r3.metric("India CCTS Revenue", f"₹{metrics['india_revenue_inr']:,.0f}/year")
r4.metric("International VCM Revenue", f"${metrics['vcm_revenue_usd']:,.0f}/year")

st.divider()
st.subheader("📈 25-Year Projection")

chart_df = projection_df.melt(
    id_vars=["Year"],
    value_vars=[
        "Cumulative CO₂ (tonnes)",
        "Cumulative Credit Revenue (₹)",
        "Cumulative Fossil Savings (₹)",
    ],
    var_name="Metric",
    value_name="Value",
)

chart = (
    alt.Chart(chart_df)
    .mark_line(point=True)
    .encode(
        x=alt.X("Year:Q", title="Year"),
        y=alt.Y("Value:Q", title="Cumulative Value"),
        color=alt.Color("Metric:N", legend=alt.Legend(title="Metric")),
        tooltip=["Year", "Metric", "Value"],
    )
    .properties(height=360)
)
st.altair_chart(chart, use_container_width=True)

st.divider()
st.subheader("🌍 ESG Score Card")

e_col, s_col, g_col, o_col = st.columns([2, 2, 2, 1])
with e_col:
    st.markdown("**E — Environment**")
    st.progress(esg["environment"] / 100)
    st.caption(f"{esg['environment']}/100 · {esg['renewable_pct']}% renewable · {metrics['co2_avoided_tonnes']} t CO₂/yr")
with s_col:
    st.markdown("**S — Social**")
    st.progress(esg["social"] / 100)
    st.caption(f"{esg['social']}/100 · ~{esg['households']} households · ~{esg['jobs']} jobs supported")
with g_col:
    st.markdown("**G — Governance**")
    st.progress(esg["governance"] / 100)
    st.caption(f"{esg['governance']}/100 · CEA compliance score")
with o_col:
    st.metric("Overall ESG", f"{esg['overall']}/100", esg["grade"])

st.divider()
st.subheader("⚖️ Comparison with Alternatives")
st.dataframe(comparison_df, use_container_width=True, hide_index=True)

st.divider()
city_slug = ctx["city_name"].replace(" ", "_")
pdf_bytes = generate_esg_pdf(
    ctx["city_name"],
    metrics,
    esg,
    projection_df,
    comparison_df,
    report_date,
)
st.download_button(
    label="📄 Download ESG Report",
    data=pdf_bytes,
    file_name=f"SolarOS_ESG_Carbon_{city_slug}_{report_date}.pdf",
    mime="application/pdf",
    use_container_width=True,
)
