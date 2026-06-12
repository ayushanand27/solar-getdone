import streamlit as st

st.set_page_config(page_title="Solar OS", layout="wide", page_icon="☀️")

if "selected_farm" not in st.session_state:
    st.session_state.selected_farm = "Jaisalmer Solar Park"

import altair as alt
import pandas as pd
import plotly.express as px

from utils.ai_engine import ai_decision
from utils.app_state import setup_app
from utils.health_score import calculate_health_score
from utils.weather import get_coordinates, get_weather

FARMS = [
    {"id": "jaisalmer", "name": "Jaisalmer Solar Park", "city": "Jaisalmer", "region": "Rajasthan"},
    {"id": "jodhpur", "name": "Jodhpur Farm", "city": "Jodhpur", "region": "Rajasthan"},
    {"id": "kutch", "name": "Kutch Solar Zone", "city": "Kutch", "region": "Gujarat"},
    {"id": "anantapur", "name": "Anantapur Farm", "city": "Anantapur", "region": "Andhra Pradesh"},
    {"id": "tumkur", "name": "Tumkur Farm", "city": "Tumkur", "region": "Karnataka"},
]

THREAT_UNDER = {"CRITICAL", "HIGH", "MEDIUM"}

FARMS_MAP = [
    {"name": "Jaisalmer Solar Park", "lat": 26.9157, "lon": 70.9083, "state": "Rajasthan"},
    {"name": "Jodhpur Farm", "lat": 26.2389, "lon": 73.0243, "state": "Rajasthan"},
    {"name": "Kutch Solar Zone", "lat": 23.7337, "lon": 69.8597, "state": "Gujarat"},
    {"name": "Anantapur Farm", "lat": 14.6819, "lon": 77.6006, "state": "Andhra Pradesh"},
    {"name": "Tumkur Farm", "lat": 13.3379, "lon": 77.1173, "state": "Karnataka"},
]

THREAT_MAP_COLORS = {
    "LOW": "#00C896",
    "MEDIUM": "#F7B731",
    "HIGH": "#EF4444",
    "CRITICAL": "#7C3AED",
}


def build_farms_map_df(all_farms):
    farm_lookup = {f["name"]: f for f in all_farms}
    rows = []
    for farm in FARMS_MAP:
        data = farm_lookup.get(farm["name"], {})
        threat_level = data.get("threat_level", "LOW")
        rows.append(
            {
                **farm,
                "solar_output": data.get("solar_output", 0),
                "shield": data.get("shield_display", data.get("shield", "—")),
                "threat_level": threat_level,
                "threat_color": THREAT_MAP_COLORS.get(threat_level, "#00C896"),
                "health_score": data.get("health_score", 50),
                "health_grade": data.get("health_grade", "🟡 Good"),
            }
        )
    return pd.DataFrame(rows)


def farms_to_map_locations(all_farms):
    map_df = build_farms_map_df(all_farms)
    return tuple(
        (
            row["name"],
            row["lat"],
            row["lon"],
            row["state"],
            row["solar_output"],
            row["shield"],
            row["threat_level"],
            row["health_score"],
            row["health_grade"],
            row["threat_color"],
        )
        for _, row in map_df.iterrows()
    )


@st.cache_data(ttl=600)
def build_farm_map(farm_locations, map_style):
    map_df = pd.DataFrame(
        farm_locations,
        columns=[
            "name",
            "lat",
            "lon",
            "state",
            "solar_output",
            "shield",
            "threat_level",
            "health_score",
            "health_grade",
            "threat_color",
        ],
    )
    fig = px.scatter_map(
        map_df,
        lat="lat",
        lon="lon",
        color="threat_level",
        size="health_score",
        size_max=35,
        hover_name="name",
        hover_data={
            "lat": False,
            "lon": False,
            "state": True,
            "solar_output": True,
            "shield": True,
            "threat_level": True,
            "health_score": True,
            "health_grade": True,
            "threat_color": False,
        },
        color_discrete_map=THREAT_MAP_COLORS,
        zoom=3.5,
        center={"lat": 20.5, "lon": 78.0},
        map_style=map_style,
    )
    fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0}, height=400)
    return fig


def render_fleet_map(all_farms, map_style):
    if st.session_state.get("last_map_style") != map_style:
        st.session_state.last_map_style = map_style
    farm_locations = farms_to_map_locations(all_farms)
    with st.spinner("Loading farm map..."):
        fig = build_farm_map(farm_locations, map_style)
        st.plotly_chart(fig, use_container_width=True)


def shield_display(shield):
    return "STANDBY" if shield == "READY" else shield


def estimate_h2_kg(radiation):
    return round(sum(r * 0.22 * 0.7 for r in radiation if r > 100) / 1000, 2)


def build_radiation_chart(hours, radiation, sim_event=None):
    chart_df = pd.DataFrame(
        {
            "Hour": [t[11:16] for t in hours],
            "Radiation (W/m²)": [float(r or 0) for r in radiation],
        }
    )
    chart_df["Estimated Output (W/m²)"] = (chart_df["Radiation (W/m²)"] * 0.22).round(1)
    if sim_event == "dust":
        chart_df["Estimated Output (W/m²)"] = (chart_df["Estimated Output (W/m²)"] * 0.75).round(1)
    hour_order = chart_df["Hour"].tolist()
    return (
        alt.Chart(chart_df)
        .mark_line(point=True, color="#F7B731")
        .encode(
            x=alt.X("Hour:N", sort=hour_order, title="Hour"),
            y=alt.Y("Estimated Output (W/m²):Q", title="Estimated Output (W/m²)", scale=alt.Scale(zero=True)),
            tooltip=["Hour", "Radiation (W/m²)", "Estimated Output (W/m²)"],
        )
        .properties(height=280)
    )


@st.cache_data(ttl=300)
def fetch_all_farms(sim_event):
    return [load_farm(farm, sim_event) for farm in FARMS]


def load_farm(farm, sim_event):
    lat, lon, city_name = get_coordinates(farm["city"])
    data = get_weather(lat, lon)
    current = data["current"]
    hourly = data["hourly"]
    radiation = [float(r or 0) for r in hourly["shortwave_radiation"]]
    hours = hourly["time"]

    status, action, mode, solar_output, shield, shield_reason, threat_level = ai_decision(
        current["weathercode"],
        current["windspeed_10m"],
        current["precipitation"],
        radiation,
        sim_event,
        hours,
    )

    h2_kg = estimate_h2_kg(radiation)
    battery_level = min(100, int(solar_output / 2))
    h2_level = min(100, int(h2_kg * 40))
    health_score, health_grade = calculate_health_score(
        solar_output,
        threat_level,
        battery_level,
        h2_level,
        shield,
        current["windspeed_10m"],
        current["precipitation"],
        current["weathercode"],
    )

    return {
        **farm,
        "city_name": city_name,
        "lat": lat,
        "lon": lon,
        "temp": current["temperature_2m"],
        "wind": current["windspeed_10m"],
        "rain": current["precipitation"],
        "wcode": current["weathercode"],
        "radiation": radiation,
        "hours": hourly["time"],
        "status": status,
        "action": action,
        "mode": mode,
        "solar_output": solar_output,
        "shield": shield,
        "shield_display": shield_display(shield),
        "shield_reason": shield_reason,
        "threat_level": threat_level,
        "h2_kg": h2_kg,
        "battery_level": battery_level,
        "h2_level": h2_level,
        "health_score": health_score,
        "health_grade": health_grade,
    }


def threat_badge(level):
    if level == "CRITICAL":
        return "🔴 CRITICAL"
    if level == "HIGH":
        return "🟠 HIGH"
    if level == "MEDIUM":
        return "🟡 MEDIUM"
    return "🟢 LOW"


def render_threat(level):
    if level == "CRITICAL":
        st.error(threat_badge(level))
    elif level == "HIGH":
        st.error(threat_badge(level))
    elif level == "MEDIUM":
        st.warning(threat_badge(level))
    else:
        st.success(threat_badge(level))


def render_farm_skeleton_cards():
    st.subheader("🏭 Farm Overview")
    cols = st.columns(len(FARMS))
    for col, farm in zip(cols, FARMS):
        with col:
            st.markdown(
                f"""
<div style="background:#161B22;border:1px solid #30363D;border-radius:10px;padding:16px;">
<div style="color:#8B949E;font-size:13px;margin-bottom:8px;">⏳ Loading…</div>
<div style="color:#E6EDF3;font-size:16px;font-weight:600;margin-bottom:12px;">{farm['name']}</div>
<div style="background:#21262D;height:10px;border-radius:4px;margin:10px 0;"></div>
<div style="background:#21262D;height:10px;border-radius:4px;width:75%;margin:10px 0;"></div>
<div style="background:#21262D;height:10px;border-radius:4px;width:55%;margin:10px 0;"></div>
</div>
""",
                unsafe_allow_html=True,
            )


def render_farm_detail(farm_data, ctx):
    d1, d2, d3, d4, d5 = st.columns(5)
    d1.metric("Solar Output", f"{farm_data['solar_output']} W/m²")
    d2.metric("Temperature", f"{farm_data['temp']}°C")
    d3.metric("Wind", f"{farm_data['wind']} km/h")
    d4.metric("H₂ Today", f"{farm_data['h2_kg']} kg")
    d5.metric("Health Score", f"{farm_data['health_score']}/100", farm_data["health_grade"])

    if farm_data["mode"] == "protection":
        st.error(f"**{farm_data['status']}** — {farm_data['action']}")
    elif farm_data["mode"] == "harvest":
        st.success(f"**{farm_data['status']}** — {farm_data['action']}")
    elif farm_data["mode"] in ("monitor", "store"):
        st.warning(f"**{farm_data['status']}** — {farm_data['action']}")
    else:
        st.info(f"**{farm_data['status']}** — {farm_data['action']}")

    s1, s2, s3 = st.columns(3)
    with s1:
        if farm_data["shield"] == "CLOSED":
            st.error(f"### 🔒 SHIELD: CLOSED\n**Reason:** {farm_data['shield_reason']}")
        elif farm_data["shield"] == "READY":
            st.warning(f"### ⚠️ SHIELD: STANDBY\n**Reason:** {farm_data['shield_reason']}")
        else:
            st.success(f"### ✅ SHIELD: OPEN\n**Reason:** {farm_data['shield_reason']}")
    with s2:
        st.markdown("### 🎯 Threat Assessment")
        render_threat(farm_data["threat_level"])
        st.caption(f"Weather code: {farm_data['wcode']} | Rain: {farm_data['rain']} mm")
    with s3:
        st.markdown("### 📍 Location")
        st.markdown(f"**Resolved:** {farm_data['city_name']}")
        st.caption(f"Lat {farm_data['lat']:.2f} | Lon {farm_data['lon']:.2f}")

    st.markdown("#### ☀️ Hourly Radiation Forecast")
    hours = farm_data.get("hours", [])
    radiation_vals = farm_data.get("radiation", [])
    if hours and radiation_vals:
        if ctx["sim_event"] == "dust":
            st.caption("⚠️ Dust storm active — showing 25% efficiency loss")
        st.altair_chart(
            build_radiation_chart(hours, radiation_vals, ctx["sim_event"]),
            use_container_width=True,
        )
    else:
        st.warning("Radiation forecast data is loading — try refreshing the page.")

    st.markdown("#### 🤖 24hr AI Decision Log")
    st.dataframe(
        pd.DataFrame(build_decision_log(farm_data["hours"], farm_data["radiation"], ctx["sim_event"])),
        use_container_width=True,
        hide_index=True,
    )


def render_farm_overview(all_farms, ctx):
    st.subheader("🏭 Farm Overview")
    cols = st.columns(len(all_farms))
    for col, farm in zip(cols, all_farms):
        selected = farm["name"] == st.session_state.selected_farm
        border_color = "#00C896" if selected else "#30363D"
        with col:
            st.markdown(
                f"""
<div style="border:{'2px' if selected else '1px'} solid {border_color};
border-radius:10px;padding:16px;margin-bottom:8px;">
<div style="color:#E6EDF3;font-size:18px;font-weight:600;">{farm['name']}</div>
<div style="color:#8B949E;font-size:12px;margin:4px 0 12px;">📍 {farm['region']}</div>
<div style="color:#F7B731;font-size:22px;font-weight:bold;">{farm['solar_output']} W/m²</div>
<div style="color:#8B949E;font-size:11px;margin-bottom:8px;">Solar Output</div>
<div style="color:#E6EDF3;font-size:13px;margin:4px 0;">Health: {farm['health_score']}/100 {farm['health_grade']}</div>
<div style="color:#E6EDF3;font-size:13px;margin:4px 0;">Shield: {farm['shield_display']}</div>
<div style="color:#E6EDF3;font-size:13px;margin:4px 0;">Energy Mode: {farm['status']}</div>
<div style="color:#E6EDF3;font-size:13px;margin:4px 0;">Threat: {threat_badge(farm['threat_level'])}</div>
<div style="color:#8B949E;font-size:12px;margin-top:8px;">🌡️ {farm['temp']}°C | 💨 {farm['wind']} km/h</div>
</div>
""",
                unsafe_allow_html=True,
            )
            if st.button("View Details", key=f"btn_{farm['name']}", use_container_width=True):
                st.session_state.selected_farm = farm["name"]
                st.rerun()

    selected_name = st.session_state.selected_farm
    farm_data = next(f for f in all_farms if f["name"] == selected_name)
    with st.expander(f"📊 {selected_name} — Details", expanded=True):
        render_farm_detail(farm_data, ctx)


def build_decision_log(hours, radiation, sim_event):
    log_rows = []
    for h, r in zip(hours, radiation):
        hour_output = round(r * 0.22 * (0.75 if sim_event == "dust" else 1), 1)
        if hour_output > 150:
            decision, sh = "⚡ Full Conversion", "🟢 Open"
        elif hour_output > 50:
            decision, sh = "🔋 Store + H₂", "🟢 Open"
        else:
            decision, sh = "🌙 Distribute", "🟢 Open"
        if sim_event == "bird":
            sh = "⚠️ Partial"
        log_rows.append(
            {"Hour": h[11:16], "Solar Output (W/m²)": hour_output, "AI Decision": decision, "Shield": sh}
        )
    return log_rows


ctx = setup_app()

st.title("🌍 Multi-Farm Dashboard")
st.caption(f"Fleet-wide solar intelligence across 5 Indian farms | Sidebar location: {ctx['city_name']}")

loading_slot = st.empty()
with loading_slot.container():
    st.info("🌍 Loading fleet data from 5 Indian farms…")
    render_farm_skeleton_cards()

with st.spinner("🌍 Fetching farm data..."):
    all_farms = fetch_all_farms(ctx["sim_event"])

loading_slot.empty()

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("### ☀️ Solar Farm Fleet — India")
with col2:
    map_style_toggle = st.radio(
        "Map Style",
        ["🌑 Dark", "🌍 Terrain"],
        horizontal=True,
        index=0,
    )

map_style = "carto-darkmatter" if map_style_toggle == "🌑 Dark" else "open-street-map"
render_fleet_map(all_farms, map_style)
st.divider()

total_output = round(sum(f["solar_output"] for f in all_farms), 1)
under_threat = sum(1 for f in all_farms if f["threat_level"] in THREAT_UNDER)
best_farm = max(all_farms, key=lambda f: f["solar_output"])
total_h2 = round(sum(f["h2_kg"] for f in all_farms), 2)

st.subheader("📊 Fleet Summary")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Fleet Output", f"{total_output} W/m²")
m2.metric("Farms Under Threat", under_threat)
m3.metric("Best Performing Farm", best_farm["name"])
m4.metric("Total H₂ Today (est.)", f"{total_h2} kg")

st.divider()
st.subheader("☀️ Solar Output Comparison")
chart_df = pd.DataFrame(
    {
        "Farm": [f["name"] for f in all_farms],
        "Solar Output (W/m²)": [f["solar_output"] for f in all_farms],
        "is_best": [f["id"] == best_farm["id"] for f in all_farms],
    }
)
chart = (
    alt.Chart(chart_df)
    .mark_bar()
    .encode(
        x=alt.X("Farm:N", sort="-y", title="Farm"),
        y=alt.Y("Solar Output (W/m²):Q", title="Solar Output (W/m²)"),
        color=alt.condition("is_best", alt.value("#22c55e"), alt.value("#3b82f6")),
        tooltip=["Farm", "Solar Output (W/m²)"],
    )
    .properties(height=320)
)
st.altair_chart(chart, use_container_width=True)

st.divider()
render_farm_overview(all_farms, ctx)
