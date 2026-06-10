import streamlit as st

st.set_page_config(page_title="Solar OS", layout="wide", page_icon="☀️")

from datetime import datetime

import plotly.graph_objects as go

from utils.app_state import setup_app

LAYER_COLORS = {
    "input": "#3B82F6",
    "ai": "#F7B731",
    "output": "#00C896",
    "cloud": "#8B5CF6",
}

PEAK_HOURS = {6, 7, 8, 9, 18, 19, 20, 21}

ctx = setup_app()

h2_kg = round(sum(r * 0.22 * 0.7 for r in ctx["radiation"] if r > 100) / 1000, 2)
battery_level = min(100, int(ctx["solar_output"] / 2))
h2_level = min(100, int(h2_kg * 40))
mqtt_status = st.session_state.get("mqtt_status", {})
mqtt_live = mqtt_status.get("success", False)
sns_count = st.session_state.get("sns_messages_today", 0)
grid_status = "Export ready" if datetime.now().hour in PEAK_HOURS else "Idle"

NODES = [
    {
        "id": "weather",
        "name": "Weather Sensors",
        "subtitle": "Open-Meteo API",
        "x": 0,
        "y": 4.2,
        "layer": "input",
        "status": f"🟢 {ctx['temp']}°C · {ctx['wind']} km/h",
    },
    {
        "id": "cv",
        "name": "CV Module",
        "subtitle": "YOLOv8n",
        "x": 0,
        "y": 2.2,
        "layer": "input",
        "status": f"{'🟡' if ctx.get('cv_threat') else '🟢'} {ctx.get('cv_threat') or 'No threat'}",
    },
    {
        "id": "ai_engine",
        "name": "AI Decision Engine",
        "subtitle": "Rule + threat fusion",
        "x": 2.5,
        "y": 3.2,
        "layer": "ai",
        "status": f"🟢 {ctx['mode'].upper()} · {ctx['threat_level']}",
    },
    {
        "id": "energy_router",
        "name": "Energy Router",
        "subtitle": "Mode orchestration",
        "x": 2.5,
        "y": 1.4,
        "layer": "ai",
        "status": f"🟢 Routing → {ctx['mode']}",
    },
    {
        "id": "shield",
        "name": "Shield Controller",
        "subtitle": "Panel protection",
        "x": 5,
        "y": 5,
        "layer": "output",
        "status": f"{'🔴' if ctx['shield'] == 'CLOSED' else '🟢'} {ctx['shield']}",
    },
    {
        "id": "battery",
        "name": "Battery Storage",
        "subtitle": "Li-ion bank",
        "x": 5,
        "y": 4,
        "layer": "output",
        "status": f"{'🟡' if battery_level < 30 else '🟢'} {battery_level}%",
    },
    {
        "id": "h2",
        "name": "H₂ Electrolyzer",
        "subtitle": "Green hydrogen",
        "x": 5,
        "y": 3,
        "layer": "output",
        "status": f"🟢 {h2_level}% · {h2_kg} kg today",
    },
    {
        "id": "grid",
        "name": "Grid Export",
        "subtitle": "ToD pricing",
        "x": 5,
        "y": 2,
        "layer": "output",
        "status": f"🟢 {grid_status}",
    },
    {
        "id": "hivemq",
        "name": "HiveMQ Cloud",
        "subtitle": "MQTT broker",
        "x": 2.5,
        "y": 5.5,
        "layer": "cloud",
        "status": f"{'🟢 Live' if mqtt_live else '🔴 Offline'}",
    },
    {
        "id": "dashboard",
        "name": "Streamlit Dashboard",
        "subtitle": "Solar OS UI",
        "x": 2.5,
        "y": 0.3,
        "layer": "cloud",
        "status": f"🟢 {ctx['city_name']}",
    },
    {
        "id": "alerts",
        "name": "Email / SNS Alerts",
        "subtitle": "AWS SNS mock",
        "x": 5,
        "y": 0.8,
        "layer": "cloud",
        "status": f"🟢 {sns_count} sent today",
    },
]

EDGES = [
    ("weather", "ai_engine"),
    ("cv", "ai_engine"),
    ("ai_engine", "shield"),
    ("ai_engine", "energy_router"),
    ("energy_router", "battery"),
    ("energy_router", "h2"),
    ("energy_router", "grid"),
    ("ai_engine", "hivemq"),
    ("weather", "hivemq"),
    ("hivemq", "dashboard"),
    ("ai_engine", "alerts"),
    ("shield", "alerts"),
]

NODE_LOOKUP = {node["id"]: node for node in NODES}


def add_arrow(fig, x0, y0, x1, y1, color="#6B7280"):
    fig.add_annotation(
        x=x1,
        y=y1,
        ax=x0,
        ay=y0,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=2,
        arrowsize=1.2,
        arrowwidth=1.5,
        arrowcolor=color,
        opacity=0.75,
    )


def build_architecture_figure():
    fig = go.Figure()

    for layer, color in LAYER_COLORS.items():
        layer_nodes = [n for n in NODES if n["layer"] == layer]
        if not layer_nodes:
            continue
        fig.add_trace(
            go.Scatter(
                x=[n["x"] for n in layer_nodes],
                y=[n["y"] for n in layer_nodes],
                mode="markers+text",
                name=layer.title(),
                marker=dict(
                    size=52,
                    color=color,
                    line=dict(width=2, color="#161B22"),
                    symbol="square",
                ),
                text=[n["name"] for n in layer_nodes],
                textposition="middle center",
                textfont=dict(size=10, color="#FFFFFF"),
                hovertext=[
                    f"<b>{n['name']}</b><br>{n['subtitle']}<br>Status: {n['status']}"
                    for n in layer_nodes
                ],
                hoverinfo="text",
            )
        )

    for src_id, dst_id in EDGES:
        src = NODE_LOOKUP[src_id]
        dst = NODE_LOOKUP[dst_id]
        add_arrow(fig, src["x"], src["y"], dst["x"], dst["y"])

    for node in NODES:
        fig.add_annotation(
            x=node["x"],
            y=node["y"] - 0.55,
            text=f"<i>{node['subtitle']}</i>",
            showarrow=False,
            font=dict(size=9, color="#8B949E"),
            yanchor="top",
        )
        fig.add_annotation(
            x=node["x"],
            y=node["y"] - 0.85,
            text=node["status"],
            showarrow=False,
            font=dict(size=9, color=LAYER_COLORS[node["layer"]]),
            yanchor="top",
        )

    fig.add_annotation(x=0, y=5.9, text="<b>INPUT / SENSING</b>", showarrow=False, font=dict(size=11, color=LAYER_COLORS["input"]))
    fig.add_annotation(x=2.5, y=5.9, text="<b>AI PROCESSING</b>", showarrow=False, font=dict(size=11, color=LAYER_COLORS["ai"]))
    fig.add_annotation(x=5, y=5.9, text="<b>OUTPUT / ACTION</b>", showarrow=False, font=dict(size=11, color=LAYER_COLORS["output"]))
    fig.add_annotation(x=2.5, y=-0.5, text="<b>CLOUD / COMMUNICATION</b>", showarrow=False, font=dict(size=11, color=LAYER_COLORS["cloud"]))

    fig.update_layout(
        title="Solar OS — System Architecture & Live Data Flow",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.8, 5.8]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.9, 6.2], scaleanchor="x", scaleratio=1),
        plot_bgcolor="#0D1117",
        paper_bgcolor="#0D1117",
        font=dict(color="#E6EDF3"),
        height=620,
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        hovermode="closest",
    )
    return fig


st.title("🏗️ System Architecture")
st.caption(f"Interactive data-flow map — live status for 📍 {ctx['city_name']}")

legend_cols = st.columns(4)
legend_items = [
    ("🔵 Input / Sensing", LAYER_COLORS["input"]),
    ("🟡 AI Processing", LAYER_COLORS["ai"]),
    ("🟢 Output / Action", LAYER_COLORS["output"]),
    ("🟣 Cloud / Communication", LAYER_COLORS["cloud"]),
]
for col, (label, color) in zip(legend_cols, legend_items):
    col.markdown(
        f'<span style="color:{color};font-weight:600;">{label}</span>',
        unsafe_allow_html=True,
    )

st.plotly_chart(build_architecture_figure(), use_container_width=True)

st.divider()
st.subheader("📋 Component Summary")

summary_cols = st.columns(3)
with summary_cols[0]:
    st.markdown("**Input Layer**")
    st.markdown(f"- Weather: `{ctx['temp']}°C`, wind `{ctx['wind']} km/h`, rain `{ctx['rain']} mm`")
    st.markdown(f"- CV threat: `{ctx.get('cv_threat') or 'None'}`")
with summary_cols[1]:
    st.markdown("**AI Layer**")
    st.markdown(f"- Mode: `{ctx['mode']}` · Threat: `{ctx['threat_level']}`")
    st.markdown(f"- Solar output: `{ctx['solar_output']} W/m²`")
with summary_cols[2]:
    st.markdown("**Output & Cloud**")
    st.markdown(f"- Shield: `{ctx['shield']}` · Battery: `{battery_level}%` · H₂: `{h2_level}%`")
    st.markdown(f"- MQTT: `{'Live' if mqtt_live else 'Offline'}` · Alerts sent: `{sns_count}`")
