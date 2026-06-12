import streamlit as st

st.set_page_config(page_title="Solar OS", layout="wide", page_icon="☀️")

from datetime import datetime

import altair as alt
import numpy as np
import pandas as pd

from utils.app_state import setup_app

from utils.grid_pricing import (
    FLAT_RATE,
    grid_price,
)


def hour_from_time(time_str):
    return int(time_str[11:13])


def solar_forecast_wm2(radiation, sim_event):
    factor = 0.75 if sim_event == "dust" else 1
    return round(radiation * 0.22 * factor, 1)


def hourly_kwh(farm_size_kw, solar_wm2):
    if solar_wm2 > 50:
        return round(farm_size_kw * 0.22, 2)
    if solar_wm2 > 0:
        return round(farm_size_kw * solar_wm2 / 1000, 2)
    return 0.0


def recommend_action(hour, solar_wm2, battery_pct):
    price, period = grid_price(hour)
    high_solar = solar_wm2 > 50
    low_solar = solar_wm2 <= 10

    if low_solar and battery_pct < 30:
        return "BUY FROM GRID", period, price
    if period == "Peak" and high_solar:
        return "EXPORT NOW", period, price
    if period == "Off-Peak" and high_solar:
        return "STORE", period, price
    if period == "Normal" and high_solar:
        return "EXPORT NOW", period, price
    if high_solar and battery_pct > 80:
        return "EXPORT NOW", period, price
    if period == "Off-Peak" and not high_solar and battery_pct < 40:
        return "BUY FROM GRID", period, price
    return "HOLD", period, price


def expected_revenue(action, kwh, price):
    if action == "EXPORT NOW":
        return round(kwh * price, 2)
    if action == "BUY FROM GRID":
        return round(-kwh * price * 0.5, 2)
    return 0.0


def build_export_plan(ctx, farm_size_kw):
    rows = []
    for time_str, radiation in zip(ctx["hours"], ctx["radiation"]):
        hour = hour_from_time(time_str)
        solar_wm2 = solar_forecast_wm2(radiation, ctx["sim_event"])
        price, period = grid_price(hour)
        battery_pct = min(100, int(solar_wm2 / 2))
        action, _, _ = recommend_action(hour, solar_wm2, battery_pct)
        kwh = hourly_kwh(farm_size_kw, solar_wm2)
        revenue = expected_revenue(action, kwh, price)
        rows.append(
            {
                "Hour": f"{hour:02d}:00",
                "Period": period,
                "Price (₹/kWh)": price,
                "Recommended Action": action,
                "Expected Revenue (₹)": revenue,
                "Solar Forecast (W/m²)": solar_wm2,
                "export_window": action == "EXPORT NOW",
            }
        )
    return pd.DataFrame(rows)


def grid_stability_score(radiation, sim_event):
    outputs = [solar_forecast_wm2(r, sim_event) for r in radiation]
    if not outputs or max(outputs) == 0:
        return 35
    mean_out = np.mean(outputs)
    std_out = np.std(outputs)
    if mean_out == 0:
        return 40
    cv = std_out / mean_out
    productive_ratio = sum(1 for o in outputs if o > 50) / len(outputs)
    score = 100 - (cv * 45) + (productive_ratio * 25)
    return int(max(10, min(100, round(score))))


def optimized_daily_revenue(plan_df):
    return round(plan_df["Expected Revenue (₹)"].clip(lower=0).sum(), 2)


def flat_daily_revenue(plan_df, farm_size_kw):
    total_kwh = sum(hourly_kwh(farm_size_kw, row["Solar Forecast (W/m²)"]) for _, row in plan_df.iterrows())
    return round(total_kwh * FLAT_RATE * 0.65, 2)


ctx = setup_app()

st.title("⚡ Grid Export Optimization")
st.caption(f"AI-driven grid export timing | 📍 {ctx['city_name']}")

current_hour = datetime.now().hour
current_price, current_period = grid_price(current_hour)
battery_level = ctx.get("battery_level", st.session_state.get("battery_level", min(100, int(ctx["solar_output"] / 2))))
current_action, _, _ = recommend_action(current_hour, ctx["solar_output"], battery_level)
stability_score = grid_stability_score(ctx["radiation"], ctx["sim_event"])

st.subheader("📊 Current Grid Demand")
g1, g2, g3, g4 = st.columns(4)
g1.metric("Current Period", current_period)
g2.metric("Grid Price Now", f"₹{current_price}/kWh")
g3.metric("Battery Level", f"{battery_level}%")
g4.metric("Grid Stability Score", f"{stability_score}/100")
st.caption(
    "Peak 6–10am & 6–10pm → ₹12 | Normal 10am–6pm → ₹7 | Off-peak 10pm–6am → ₹3"
)

st.subheader("🤖 AI Export Recommendation")
if current_action == "EXPORT NOW":
    st.success(
        f"**{current_action}** — Peak/normal pricing (₹{current_price}/kWh) with "
        f"{ctx['solar_output']} W/m² solar. Export surplus to maximize revenue."
    )
elif current_action == "STORE":
    st.warning(
        f"**{current_action}** — Off-peak rates (₹{current_price}/kWh) but strong solar "
        f"({ctx['solar_output']} W/m²). Store energy for peak export windows."
    )
elif current_action == "BUY FROM GRID":
    st.error(
        f"**{current_action}** — Low solar ({ctx['solar_output']} W/m²) and battery at "
        f"{battery_level}%. Import from grid until production recovers."
    )
else:
    st.info(
        f"**{current_action}** — Monitor conditions. Solar: {ctx['solar_output']} W/m² | "
        f"Battery: {battery_level}% | Price: ₹{current_price}/kWh"
    )

st.divider()
st.subheader("💰 Revenue Calculator")
farm_size = st.slider("Farm Size (kW)", 10, 10000, 500, 10, key="grid_farm_size")
plan_df = build_export_plan(ctx, farm_size)

daily_optimized = optimized_daily_revenue(plan_df)
daily_flat = flat_daily_revenue(plan_df, farm_size)
monthly_optimized = round(daily_optimized * 30, 2)
monthly_flat = round(daily_flat * 30, 2)
annual_optimized = round(daily_optimized * 365, 2)
annual_flat = round(daily_flat * 365, 2)

r1, r2, r3 = st.columns(3)
with r1:
    st.metric("Daily Revenue (Optimized)", f"₹{daily_optimized:,.0f}", f"+₹{daily_optimized - daily_flat:,.0f} vs flat")
    st.caption(f"Flat rate estimate: ₹{daily_flat:,.0f}")
with r2:
    st.metric("Monthly Revenue (Optimized)", f"₹{monthly_optimized:,.0f}", f"+₹{monthly_optimized - monthly_flat:,.0f} vs flat")
    st.caption(f"Flat rate estimate: ₹{monthly_flat:,.0f}")
with r3:
    st.metric("Annual Revenue (Optimized)", f"₹{annual_optimized:,.0f}", f"+₹{annual_optimized - annual_flat:,.0f} vs flat")
    st.caption(f"Flat rate estimate: ₹{annual_flat:,.0f}")

st.info(
    f"Solar OS time-of-day optimization adds **₹{annual_optimized - annual_flat:,.0f}/year** "
    f"vs flat ₹{FLAT_RATE}/kWh export (Grid Stability Score: **{stability_score}/100** — "
    "higher scores unlock better grid trust and tariff bonuses)."
)

st.divider()
st.subheader("📈 24-Hour Price vs Solar Forecast")
band_df = plan_df.assign(Band=plan_df["export_window"].astype(int) * plan_df["Price (₹/kWh)"].max())

export_highlight = (
    alt.Chart(band_df)
    .mark_bar(color="#22c55e", opacity=0.18)
    .encode(
        x=alt.X("Hour:N", sort=None),
        y=alt.Y("Band:Q", axis=None, scale=alt.Scale(domain=[0, max(band_df["Band"].max(), 1)])),
    )
)
price_chart = (
    alt.Chart(plan_df)
    .mark_line(strokeWidth=2, color="#f97316")
    .encode(
        x=alt.X("Hour:N", sort=None, title="Hour"),
        y=alt.Y("Price (₹/kWh):Q", title="Grid Price (₹/kWh)", axis=alt.Axis(titleColor="#f97316")),
        tooltip=["Hour", "Price (₹/kWh)", "Period"],
    )
)
solar_chart = (
    alt.Chart(plan_df)
    .mark_line(strokeWidth=2, color="#3b82f6")
    .encode(
        x=alt.X("Hour:N", sort=None),
        y=alt.Y(
            "Solar Forecast (W/m²):Q",
            title="Solar Forecast (W/m²)",
            axis=alt.Axis(titleColor="#3b82f6", orient="right"),
        ),
        tooltip=["Hour", "Solar Forecast (W/m²)"],
    )
)
combined_chart = alt.layer(export_highlight, price_chart, solar_chart).resolve_scale(y="independent").properties(height=360)
st.altair_chart(combined_chart, use_container_width=True)
st.caption("Green bands = AI export windows (EXPORT NOW hours)")

st.divider()
st.subheader("📋 24hr Export Plan")
display_df = plan_df[
    ["Hour", "Price (₹/kWh)", "Recommended Action", "Expected Revenue (₹)", "Solar Forecast (W/m²)"]
].copy()
st.dataframe(display_df, use_container_width=True, hide_index=True)
