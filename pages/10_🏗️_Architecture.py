import streamlit as st

st.set_page_config(page_title="Solar OS", layout="wide", page_icon="☀️")

from datetime import datetime

import plotly.graph_objects as go

from utils.app_state import setup_app
from utils.weather import current_hour_ist

LAYER_COLORS = {
    "input": "#3B82F6",
    "ai": "#F7B731",
    "output": "#00C896",
    "cloud": "#8B5CF6",
    "edge": "#F97316",
}

LAYER_LABELS = {
    "input": "Input",
    "ai": "AI Processing",
    "output": "Output",
    "cloud": "Cloud",
    "edge": "Edge / IoT",
}

PEAK_HOURS = {6, 7, 8, 9, 18, 19, 20, 21}

ctx = setup_app()

h2_kg = round(sum(r * 0.22 * 0.7 for r in ctx["radiation"] if r > 100) / 1000, 2)
battery_level = min(100, int(ctx["solar_output"] / 2))
h2_level = min(100, int(h2_kg * 40))
mqtt_status = st.session_state.get("mqtt_status", {})
mqtt_live = mqtt_status.get("success", False)
sns_count = st.session_state.get("sns_messages_today", 0)
grid_status = "Export ready" if current_hour_ist() in PEAK_HOURS else "Idle"
cv_label = ctx.get("cv_threat") or "Idle"
edge_latency = ctx.get("edge_latency", 72)

if ctx["shield"] == "CLOSED":
    shield_dot, shield_color = "●", "#EF4444"
elif ctx["shield"] == "READY":
    shield_dot, shield_color = "●", "#F7B731"
else:
    shield_dot, shield_color = "●", "#00C896"

NODES = [
    {
        "id": "weather",
        "name": "Weather Sensors",
        "subtitle": "Open-Meteo API",
        "x": 1,
        "y": 9,
        "layer": "input",
        "status": f"● {ctx['temp']}°C",
        "status_color": "#00C896",
    },
    {
        "id": "cv",
        "name": "CV Module",
        "subtitle": "YOLOv8n",
        "x": 1,
        "y": 6,
        "layer": "input",
        "status": f"● {cv_label}",
        "status_color": "#F7B731" if ctx.get("cv_threat") else "#00C896",
    },
    {
        "id": "iot",
        "name": "IoT Sensors",
        "subtitle": "Edge telemetry",
        "x": 1,
        "y": 3,
        "layer": "edge",
        "status": f"● {edge_latency}ms",
        "status_color": "#F97316",
    },
    {
        "id": "ai_engine",
        "name": "AI Decision Engine",
        "subtitle": "Rule + threat fusion",
        "x": 3,
        "y": 10,
        "layer": "ai",
        "status": f"● {ctx['mode'].upper()}",
        "status_color": "#F7B731",
    },
    {
        "id": "threat_assessor",
        "name": "Threat Assessor",
        "subtitle": "Risk scoring",
        "x": 3,
        "y": 7.5,
        "layer": "ai",
        "status": f"● {ctx['threat_level']}",
        "status_color": "#EF4444" if ctx["threat_level"] in ("HIGH", "CRITICAL") else "#F7B731",
    },
    {
        "id": "energy_router",
        "name": "Energy Router",
        "subtitle": "Mode orchestration",
        "x": 3,
        "y": 5,
        "layer": "ai",
        "status": f"● {ctx['status'][:18]}",
        "status_color": "#F7B731",
    },
    {
        "id": "health_monitor",
        "name": "Health Monitor",
        "subtitle": "Farm health score",
        "x": 3,
        "y": 2.5,
        "layer": "ai",
        "status": f"● {ctx.get('solar_output', 0)} W/m²",
        "status_color": "#00C896",
    },
    {
        "id": "shield",
        "name": "Shield Controller",
        "subtitle": "Panel protection",
        "x": 5,
        "y": 10,
        "layer": "output",
        "status": f"{shield_dot} {ctx['shield']}",
        "status_color": shield_color,
    },
    {
        "id": "battery",
        "name": "Battery Storage",
        "subtitle": "Li-ion bank",
        "x": 5,
        "y": 7.5,
        "layer": "output",
        "status": f"● {battery_level}%",
        "status_color": "#F7B731" if battery_level < 30 else "#00C896",
    },
    {
        "id": "h2",
        "name": "H₂ Electrolyzer",
        "subtitle": "Green hydrogen",
        "x": 5,
        "y": 5,
        "layer": "output",
        "status": f"● {h2_kg} kg today",
        "status_color": "#00C896",
    },
    {
        "id": "grid",
        "name": "Grid Export",
        "subtitle": "Time-of-day pricing",
        "x": 5,
        "y": 2.5,
        "layer": "output",
        "status": f"● {grid_status}",
        "status_color": "#00C896",
    },
    {
        "id": "hivemq",
        "name": "HiveMQ MQTT",
        "subtitle": "Cloud broker",
        "x": 7,
        "y": 10,
        "layer": "cloud",
        "status": "● Live" if mqtt_live else "● Offline",
        "status_color": "#00C896" if mqtt_live else "#EF4444",
    },
    {
        "id": "greengrass",
        "name": "AWS IoT Greengrass",
        "subtitle": "Edge sync",
        "x": 7,
        "y": 7.5,
        "layer": "cloud",
        "status": "● Synced" if not ctx.get("edge_mode") else "● Edge",
        "status_color": "#8B5CF6",
    },
    {
        "id": "alerts",
        "name": "Email / SNS Alerts",
        "subtitle": "AWS SNS mock",
        "x": 7,
        "y": 5,
        "layer": "cloud",
        "status": f"● {sns_count} sent",
        "status_color": "#8B5CF6",
    },
    {
        "id": "dashboard",
        "name": "Streamlit Dashboard",
        "subtitle": "Solar OS UI",
        "x": 7,
        "y": 2.5,
        "layer": "cloud",
        "status": f"● {ctx['city_name']}",
        "status_color": "#00C896",
    },
]

EDGES = [
    ("weather", "ai_engine"),
    ("cv", "threat_assessor"),
    ("iot", "ai_engine"),
    ("threat_assessor", "ai_engine"),
    ("ai_engine", "energy_router"),
    ("ai_engine", "health_monitor"),
    ("ai_engine", "shield"),
    ("energy_router", "battery"),
    ("energy_router", "h2"),
    ("energy_router", "grid"),
    ("health_monitor", "dashboard"),
    ("ai_engine", "hivemq"),
    ("weather", "hivemq"),
    ("hivemq", "greengrass"),
    ("hivemq", "dashboard"),
    ("shield", "alerts"),
    ("ai_engine", "alerts"),
]

NODE_LOOKUP = {node["id"]: node for node in NODES}
MARKER_SIZE = 45
NODE_PAD = 0.45


def layer_color(layer):
    return LAYER_COLORS.get(layer, "#6B7280")


def edge_endpoints(x0, y0, x1, y1, pad=NODE_PAD):
    dx, dy = x1 - x0, y1 - y0
    length = (dx**2 + dy**2) ** 0.5 or 1.0
    ux, uy = dx / length, dy / length
    return (
        x0 + ux * pad,
        y0 + uy * pad,
        x1 - ux * pad,
        y1 - uy * pad,
    )


def add_edge(fig, src_id, dst_id):
    src = NODE_LOOKUP[src_id]
    dst = NODE_LOOKUP[dst_id]
    color = layer_color(src["layer"])
    x0, y0, x1, y1 = edge_endpoints(src["x"], src["y"], dst["x"], dst["y"])

    fig.add_trace(
        go.Scatter(
            x=[x0, x1],
            y=[y0, y1],
            mode="lines",
            line=dict(color=color, width=2),
            hoverinfo="skip",
            showlegend=False,
        )
    )
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
        arrowsize=1.4,
        arrowwidth=2,
        arrowcolor=color,
        opacity=0.95,
    )


def build_architecture_figure():
    fig = go.Figure()

    for edge in EDGES:
        add_edge(fig, edge[0], edge[1])

    for layer in ("input", "edge", "ai", "output", "cloud"):
        layer_nodes = [n for n in NODES if n["layer"] == layer]
        if not layer_nodes:
            continue
        color = layer_color(layer)
        fig.add_trace(
            go.Scatter(
                x=[n["x"] for n in layer_nodes],
                y=[n["y"] for n in layer_nodes],
                mode="markers",
                name=LAYER_LABELS[layer],
                marker=dict(
                    size=MARKER_SIZE,
                    color=color,
                    line=dict(width=3, color="#E6EDF3"),
                    symbol="circle",
                    opacity=0.95,
                ),
                hovertext=[
                    f"<b>{n['name']}</b><br>{n['subtitle']}<br>{n['status']}"
                    for n in layer_nodes
                ],
                hoverinfo="text",
            )
        )

    column_headers = [
        (1, "INPUT / SENSING", LAYER_COLORS["input"]),
        (3, "AI PROCESSING", LAYER_COLORS["ai"]),
        (5, "OUTPUT / ACTION", LAYER_COLORS["output"]),
        (7, "CLOUD / COMM", LAYER_COLORS["cloud"]),
    ]
    for x, label, color in column_headers:
        fig.add_annotation(
            x=x,
            y=11.5,
            text=f"<b>{label}</b>",
            showarrow=False,
            font=dict(size=12, color=color),
            yanchor="bottom",
        )

    for node in NODES:
        fig.add_annotation(
            x=node["x"],
            y=node["y"],
            text=f"<b>{node['name']}</b>",
            showarrow=False,
            font=dict(size=12, color="#FFFFFF"),
            yanchor="bottom",
            yshift=30,
        )
        fig.add_annotation(
            x=node["x"],
            y=node["y"],
            text=node["subtitle"],
            showarrow=False,
            font=dict(size=12, color="#8B949E"),
            yanchor="top",
            yshift=-40,
        )
        fig.add_annotation(
            x=node["x"],
            y=node["y"],
            text=node["status"],
            showarrow=False,
            font=dict(size=12, color=node["status_color"]),
            yanchor="top",
            yshift=-55,
        )

    fig.update_layout(
        title=dict(
            text="Solar OS — System Architecture<br>"
            "<sup style='color:#8B949E'>Real-time Edge AI Pipeline</sup>",
            x=0.5,
            xanchor="center",
            font=dict(size=20, color="#E6EDF3"),
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            showline=False,
            range=[-0.2, 8.2],
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            showline=False,
            range=[-0.5, 12.5],
            scaleanchor="x",
            scaleratio=1,
        ),
        plot_bgcolor="#0D1117",
        paper_bgcolor="#0D1117",
        font=dict(color="#E6EDF3"),
        height=850,
        margin=dict(l=30, r=30, t=90, b=30),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.08,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11, color="#E6EDF3"),
        ),
        hovermode="closest",
    )
    return fig


st.title("🏗️ System Architecture")
st.caption(f"Interactive data-flow map — live status for 📍 {ctx['city_name']}")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Nodes", len(NODES))
m2.metric("Active Connections", len(EDGES))
m3.metric("Live Data Streams", 4)
m4.metric("Edge Latency", f"{edge_latency}ms")

st.plotly_chart(build_architecture_figure(), use_container_width=True)

legend_cols = st.columns(5)
legend_items = [
    ("Input", LAYER_COLORS["input"]),
    ("AI Processing", LAYER_COLORS["ai"]),
    ("Output", LAYER_COLORS["output"]),
    ("Cloud", LAYER_COLORS["cloud"]),
    ("Live Data", "#00C896"),
]
for col, (label, color) in zip(legend_cols, legend_items):
    col.markdown(
        f"""
<div style="display:flex;align-items:center;gap:8px;justify-content:center;">
<span style="display:inline-block;width:16px;height:16px;background:{color};
border-radius:3px;border:1px solid #30363D;"></span>
<span style="color:#E6EDF3;font-size:13px;">{label}</span>
</div>
""",
        unsafe_allow_html=True,
    )

st.divider()
st.subheader("📋 Component Summary")

summary_cols = st.columns(3)
with summary_cols[0]:
    st.markdown("**Input Layer**")
    st.markdown(f"- Weather: `{ctx['temp']}°C`, wind `{ctx['wind']} km/h`, rain `{ctx['rain']} mm`")
    st.markdown(f"- CV threat: `{ctx.get('cv_threat') or 'None'}`")
    st.markdown(f"- IoT latency: `{edge_latency}ms`")
with summary_cols[1]:
    st.markdown("**AI Layer**")
    st.markdown(f"- Mode: `{ctx['mode']}` · Threat: `{ctx['threat_level']}`")
    st.markdown(f"- Solar output: `{ctx['solar_output']} W/m²`")
with summary_cols[2]:
    st.markdown("**Output & Cloud**")
    st.markdown(f"- Shield: `{ctx['shield']}` · Battery: `{battery_level}%` · H₂: `{h2_level}%`")
    st.markdown(f"- MQTT: `{'Live' if mqtt_live else 'Offline'}` · Alerts sent: `{sns_count}`")
