import random
import time
from datetime import datetime

import streamlit as st
from PIL import Image

from utils.ai_engine import ai_decision, apply_sim_overrides
from utils.auth import check_auth
from utils.cv_module import SAMPLE_IMAGES, SAMPLES_DIR, run_cv_detection
from utils.grid_pricing import current_grid_tier
from utils.health_score import calculate_health_score
from utils.weather import get_7day, get_coordinates, get_weather


AUTO_SIM_POOL = [None, None, None, "bird", "dust", "bird", "dust"]


def _pick_auto_sim_event():
    cycle = int(time.time()) // 5
    if st.session_state.get("auto_sim_cycle") != cycle:
        st.session_state.auto_sim_cycle = cycle
        random.seed(cycle)
        st.session_state.sim_event = random.choice(AUTO_SIM_POOL)
    return st.session_state.get("sim_event")


@st.fragment(run_every=5)
def _auto_sim_scheduler():
    if st.session_state.get("auto_sim_toggle"):
        _pick_auto_sim_event()
        st.rerun()


def init_session_state():
    defaults = {
        "city": "Jaipur",
        "sim_event": None,
        "cv_threat": None,
        "edge_mode": False,
        "lat": 26.9124,
        "lon": 75.7873,
        "city_name": "Jaipur",
        "edge_start_time": time.time(),
        "edge_decision_log": [],
        "auto_sim": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_sidebar():
    st.sidebar.title("📍 Location")
    city = st.sidebar.text_input("Enter City", value=st.session_state.city, key="city_input")
    st.session_state.city = city

    st.sidebar.divider()
    st.sidebar.title("🧪 Threat Simulator")
    auto_sim = st.sidebar.toggle("⚡ Auto Simulation", value=False, key="auto_sim_toggle")
    st.sidebar.caption("Auto generates random threat events every 5s")
    bird_active = st.sidebar.toggle(
        "🐦 Bird Attack", value=False, key="bird_sim_toggle", disabled=auto_sim
    )
    dust_active = st.sidebar.toggle(
        "🌫️ Dust Storm", value=False, key="dust_sim_toggle", disabled=auto_sim
    )

    if auto_sim:
        sim_event = _pick_auto_sim_event()
    elif bird_active:
        sim_event = "bird"
    elif dust_active:
        sim_event = "dust"
    else:
        sim_event = None

    if auto_sim:
        st.sidebar.warning("⚡ Auto simulation ON — cycling every 5s")
        if sim_event == "bird":
            st.sidebar.error("🐦 Bird activity detected!")
        elif sim_event == "dust":
            st.sidebar.error("🌫️ Dust storm detected!")
        else:
            st.sidebar.info("✅ No threat this cycle")
    elif sim_event == "bird":
        st.sidebar.error("🐦 Bird activity detected!")
    elif sim_event == "dust":
        st.sidebar.error("🌫️ Dust storm detected!")
    else:
        st.sidebar.success("✅ No simulated threats")

    st.sidebar.divider()
    st.sidebar.title("🔬 CV Detection")
    cv_source = st.sidebar.radio(
        "Image Source",
        ["📁 Use Sample Image", "📤 Upload My Image"],
        index=1,
        key="cv_source",
    )
    cv_image = None
    cv_filename = None

    if cv_source == "📁 Use Sample Image":
        sample_options = ["— Select —", *SAMPLE_IMAGES]
        sample_choice = st.sidebar.selectbox(
            "Select Sample",
            sample_options,
            index=0,
            key="cv_sample_choice",
        )
        if sample_choice != "— Select —":
            sample_path = SAMPLES_DIR / sample_choice
            if sample_path.exists():
                cv_filename = sample_choice
                cv_image = Image.open(sample_path).convert("RGB")
    else:
        uploaded_file = st.sidebar.file_uploader("Upload Image", type=["png", "jpg", "jpeg"], key="cv_upload")
        if uploaded_file is not None:
            cv_filename = uploaded_file.name
            cv_image = Image.open(uploaded_file).convert("RGB")

    cv_threat = None
    cv_confidence = None
    cv_display_image = None
    cv_verdict = "LOW"
    cv_explanation = "Select or upload an image to run CV threat detection."
    cv_detections = []

    if cv_image is not None:
        is_sample = cv_source == "📁 Use Sample Image"
        cv_threat, cv_confidence, cv_display_image, cv_verdict, cv_explanation, cv_detections = run_cv_detection(
            cv_image, cv_filename, is_sample
        )
        if cv_threat == "bird":
            sim_event = "bird"
        elif cv_threat == "dust":
            sim_event = "dust"

    st.session_state.sim_event = sim_event
    st.session_state.cv_threat = cv_threat
    st.session_state.auto_sim = auto_sim

    st.sidebar.divider()
    st.sidebar.title("⚡ Edge Node")
    edge_mode = st.sidebar.toggle("🖥️ Edge Mode", value=st.session_state.edge_mode, key="edge_mode_toggle")
    st.session_state.edge_mode = edge_mode

    edge_latency = random.randint(45, 95)
    edge_cpu = random.randint(18, 34)
    edge_memory_used = 312
    edge_memory_total = 4096

    if edge_mode:
        st.sidebar.success("🟢 RPi4-ARM64 ONLINE")
        st.sidebar.metric("Inference Latency", f"{edge_latency} ms")
        st.sidebar.metric("CPU Usage", f"{edge_cpu}%")
        st.sidebar.caption(f"Memory: {edge_memory_used} MB / {edge_memory_total} MB")
    else:
        st.sidebar.info("☁️ Cloud Mode")

    lat, lon, city_name = get_coordinates(city)
    st.session_state.lat = lat
    st.session_state.lon = lon
    st.session_state.city_name = city_name
    st.sidebar.success(f"📍 Showing data for: {city_name}")

    return {
        "city": city,
        "city_name": city_name,
        "lat": lat,
        "lon": lon,
        "sim_event": sim_event,
        "auto_sim": auto_sim,
        "cv_source": cv_source,
        "cv_filename": cv_filename,
        "cv_threat": cv_threat,
        "cv_confidence": cv_confidence,
        "cv_display_image": cv_display_image,
        "cv_verdict": cv_verdict,
        "cv_explanation": cv_explanation,
        "cv_detections": cv_detections,
        "edge_mode": edge_mode,
        "edge_latency": edge_latency,
        "edge_cpu": edge_cpu,
        "edge_memory_used": edge_memory_used,
        "edge_memory_total": edge_memory_total,
    }


def setup_app():
    check_auth()
    init_session_state()
    sidebar = render_sidebar()

    data = get_weather(sidebar["lat"], sidebar["lon"])
    current = data["current"]
    hourly = data["hourly"]

    temp = current["temperature_2m"]
    wind = current["windspeed_10m"]
    rain = current["precipitation"]
    wcode = current["weathercode"]
    radiation = [float(r or 0) for r in hourly["shortwave_radiation"]]
    hours = hourly["time"]

    sim_event = st.session_state.get("sim_event")
    status, action, mode, solar_output, shield, shield_reason, threat_level = ai_decision(
        wcode, wind, rain, radiation, sim_event, hours
    )
    if sim_event in ("bird", "dust") and shield != "CLOSED":
        status, action, mode, solar_output, shield, shield_reason, threat_level = apply_sim_overrides(
            sim_event,
            status,
            action,
            mode,
            solar_output,
            shield,
            shield_reason,
            threat_level,
            radiation,
            hours,
        )

    h2_kg = round(sum(r * 0.22 * 0.7 for r in radiation if r > 100) / 1000, 2)
    battery_level = min(100, int(solar_output / 2))
    h2_level = min(100, int(h2_kg * 40))
    health_score, health_grade = calculate_health_score(
        solar_output,
        threat_level,
        battery_level,
        h2_level,
        shield,
        wind,
        rain,
        wcode,
    )
    grid_tier = current_grid_tier()

    st.session_state.battery_level = battery_level
    st.session_state.h2_kg = h2_kg
    st.session_state.h2_level = h2_level
    st.session_state.shield_status = shield
    st.session_state.health_score = health_score
    st.session_state.health_grade = health_grade
    st.session_state.grid_price = grid_tier["price"]
    st.session_state.grid_period = grid_tier["period"]

    if sidebar["edge_mode"]:
        edge_log = st.session_state.edge_decision_log
        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "decision": status,
            "latency_ms": sidebar["edge_latency"],
        }
        if not edge_log or edge_log[-1]["decision"] != status:
            edge_log.append(entry)
        st.session_state.edge_decision_log = edge_log[-5:]

    forecast = get_7day(sidebar["lat"], sidebar["lon"])

    ctx = {
        **sidebar,
        "temp": temp,
        "wind": wind,
        "rain": rain,
        "wcode": wcode,
        "radiation": radiation,
        "hours": hours,
        "status": status,
        "action": action,
        "mode": mode,
        "solar_output": solar_output,
        "shield": shield,
        "shield_reason": shield_reason,
        "threat_level": threat_level,
        "forecast": forecast,
        "battery_level": battery_level,
        "h2_kg": h2_kg,
        "h2_level": h2_level,
        "health_score": health_score,
        "health_grade": health_grade,
        "grid_price": grid_tier["price"],
        "grid_period": grid_tier["period"],
    }

    if sidebar["auto_sim"]:
        _auto_sim_scheduler()

    return ctx


def render_edge_banner(ctx):
    if ctx["edge_mode"]:
        st.success(
            f"⚡ **EDGE MODE ACTIVE** — Decisions running locally on RPi4-ARM64 "
            f"| Latency: {ctx['edge_latency']}ms | No cloud dependency"
        )
    else:
        st.info("☁️ **CLOUD MODE** — Decisions synced via AWS IoT Greengrass")
