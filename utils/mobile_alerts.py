import random
from datetime import datetime

import streamlit as st

SNS_TOPIC_ARN = "arn:aws:sns:ap-south-1:solar-os-alerts"
SNS_COST_PER_MESSAGE = 0.0000005
PEAK_HOURS = {6, 7, 8, 9, 18, 19, 20, 21}
CHANNELS = ["SMS", "Email", "Push"]


def init_alert_state():
    if "alert_log" not in st.session_state:
        st.session_state.alert_log = []
    if "sns_messages_today" not in st.session_state:
        st.session_state.sns_messages_today = 0
    if "last_auto_alert_key" not in st.session_state:
        st.session_state.last_auto_alert_key = None
    if "last_email_status" not in st.session_state:
        st.session_state.last_email_status = None


def maybe_send_email(alert_type, message):
    if not st.session_state.get("alert_email_enabled"):
        return
    to_email = st.session_state.get("alert_email", "").strip()
    if not to_email:
        st.session_state.last_email_status = "❌ Email failed: no recipient address"
        return
    try:
        from utils.email_alerts import send_email_alert

        send_email_alert(alert_type, message, to_email)
        st.session_state.last_email_status = f"✅ Email sent to {to_email}"
    except Exception as exc:
        st.session_state.last_email_status = f"❌ Email failed: {exc}"


def append_alert(alert_type, message, channel=None, status="✅ Delivered"):
    init_alert_state()
    channel = channel or _pick_channel()
    log = st.session_state.alert_log
    if log and log[-1]["Type"] == alert_type and log[-1]["Message"] == message:
        return False

    entry = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Type": alert_type,
        "Message": message,
        "Channel": channel,
        "Status": status,
    }
    log.append(entry)
    st.session_state.alert_log = log[-10:]
    st.session_state.sns_messages_today += 1
    st.session_state.latest_alert_preview = message
    maybe_send_email(alert_type, message)
    return True


def _pick_channel():
    return random.choice(CHANNELS)


def _auto_once(key, alert_type, message, enabled=True):
    try:
        if not enabled:
            return
        if st.session_state.last_auto_alert_key == key:
            return
        if append_alert(alert_type, message):
            st.session_state.last_auto_alert_key = key
    except Exception:
        pass


def battery_level(solar_output):
    return min(100, int(solar_output / 2))


def h2_tank_level(radiation):
    h2_stored = round(sum(r * 0.22 * 0.7 for r in radiation if r > 100) / 1000, 2)
    return min(100, int(h2_stored * 40))


def render_alert_config():
    init_alert_state()
    st.markdown("#### Alert Types")
    c1, c2 = st.columns(2)
    with c1:
        storm = st.checkbox("☑ Storm alerts", value=True, key="alert_storm")
        bird_dust = st.checkbox("☑ Bird/dust CV detection", value=True, key="alert_bird_dust")
        battery = st.checkbox("☑ Battery critical (<20%)", value=True, key="alert_battery")
    with c2:
        h2_full = st.checkbox("☑ H₂ tank full", value=True, key="alert_h2_full")
        peak = st.checkbox("☑ Peak pricing window (grid export)", value=True, key="alert_peak")
    return {
        "storm": storm,
        "bird_dust": bird_dust,
        "battery": battery,
        "h2_full": h2_full,
        "peak": peak,
    }


def process_auto_alerts(ctx, config):
    try:
        if ctx is None:
            return
        if not isinstance(ctx, dict):
            return
        if config is None:
            return

        init_alert_state()
        city = ctx.get("city_name", "Farm")
        sim = ctx.get("sim_event")
        cv_threat = ctx.get("cv_threat")
        effective_sim = sim
        if cv_threat in ("bird", "dust"):
            effective_sim = cv_threat

        if effective_sim != st.session_state.get("last_sim_event"):
            st.session_state.last_auto_alert_key = None
            st.session_state.last_sim_event = effective_sim

        if effective_sim == "bird" and config.get("bird_dust"):
            _auto_once(
                "bird",
                "CV Detection",
                f"Bird activity detected at {city}. Shield partially closed. Check dashboard.",
                config["bird_dust"],
            )
        elif effective_sim == "dust" and config.get("bird_dust"):
            _auto_once(
                "dust",
                "CV Detection",
                f"Dust storm detected at {city}. Auto-clean initiated. 25% efficiency loss.",
                config["bird_dust"],
            )

        if ctx.get("wcode", 0) >= 95 and config.get("storm"):
            _auto_once(
                "storm",
                "Storm",
                f"Thunderstorm alert at {city}. Shield closed — panels protected.",
                config["storm"],
            )

        batt = ctx.get("battery_level")
        if batt is None:
            batt = battery_level(ctx.get("solar_output", 0))
        if batt < 20 and config.get("battery"):
            _auto_once(
                f"battery_{batt}",
                "Battery",
                f"Battery critical ({batt}%) at {city}. Prioritizing charge from grid/solar.",
                config["battery"],
            )

        h2 = ctx.get("h2_level")
        if h2 is None:
            h2 = h2_tank_level(ctx.get("radiation", []))
        if h2 > 80 and config.get("h2_full"):
            _auto_once(
                f"h2_{h2}",
                "H₂ Tank",
                f"H₂ tank nearly full ({h2}%) at {city}. Redirect surplus to grid export.",
                config["h2_full"],
            )

        hour = datetime.now().hour
        if hour in PEAK_HOURS and config.get("peak"):
            _auto_once(
                f"peak_{hour}",
                "Grid Export",
                f"Peak pricing window active (₹12/kWh) at {city}. Export surplus now.",
                config["peak"],
            )
    except Exception:
        pass


def send_test_alert(city_name):
    append_alert(
        "Test",
        f"Test alert from Solar OS — {city_name} farm online and monitoring.",
        channel="Push",
        status="📤 Sending",
    )


def latest_phone_message(ctx):
    preview = st.session_state.get("latest_alert_preview")
    if preview:
        return preview
    sim = ctx.get("sim_event")
    if ctx.get("cv_threat") in ("bird", "dust"):
        sim = ctx["cv_threat"]
    if sim == "bird":
        return f"Bird activity detected at {ctx['city_name']}. Shield partially closed. Check dashboard."
    if sim == "dust":
        return f"Dust storm detected at {ctx['city_name']}. Auto-clean initiated."
    return f"All systems normal at {ctx['city_name']}. Solar output {ctx['solar_output']} W/m²."


def sns_estimated_cost(message_count):
    return round(message_count * SNS_COST_PER_MESSAGE, 7)
