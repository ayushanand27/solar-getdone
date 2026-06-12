import json
from datetime import datetime

import streamlit as st

BROKER_HOST = "localhost"
BROKER_PORT = 1883


def _energy_mode_label(ctx):
    mapping = {
        "harvest": "Full Conversion",
        "store": "Store+H2",
        "distribute": "Distribute",
        "protection": "Shield Protected",
        "monitor": "Monitoring",
    }
    return mapping.get(ctx["mode"], ctx["status"])


def _alert_level(threat_level, sim_event=None):
    if threat_level in ("CRITICAL", "HIGH"):
        return "HIGH"
    if threat_level == "MEDIUM" or sim_event in ("bird", "dust"):
        return "MEDIUM"
    return "LOW"


def _build_topic_payloads(ctx):
    sim_event = ctx.get("sim_event")
    return [
        (
            "solar/weather",
            {"temp": ctx["temp"], "wind": ctx["wind"], "rain": ctx["rain"]},
        ),
        (
            "solar/shield",
            {"status": ctx["shield"], "reason": ctx["shield_reason"]},
        ),
        (
            "solar/energy_mode",
            {
                "mode": _energy_mode_label(ctx),
                "battery": ctx.get("battery_level", st.session_state.get("battery_level")),
                "h2_level": ctx.get("h2_level", st.session_state.get("h2_level")),
            },
        ),
        (
            "solar/alerts",
            {
                "level": _alert_level(ctx["threat_level"], sim_event),
                "message": ctx["action"],
                "sim_event": sim_event,
            },
        ),
    ]


def _probe_broker():
    try:
        import paho.mqtt.client as mqtt

        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=5)
        client.disconnect()
        return True
    except Exception:
        return False


def _publish_via_paho(topic, payload_str):
    import paho.mqtt.client as mqtt

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=5)
    client.publish(topic, payload_str, qos=0)
    client.disconnect()
    return "✅ Published"


def publish_mqtt_messages(ctx):
    if "mqtt_feed" not in st.session_state:
        st.session_state.mqtt_feed = []
    if "mqtt_broker_available" not in st.session_state:
        st.session_state.mqtt_broker_available = _probe_broker()
    if "mqtt_mock_queue" not in st.session_state:
        st.session_state.mqtt_mock_queue = []

    timestamp = datetime.now().strftime("%H:%M:%S")
    new_entries = []

    for topic, payload in _build_topic_payloads(ctx):
        payload_str = json.dumps(payload)
        if st.session_state.mqtt_broker_available:
            try:
                status = _publish_via_paho(topic, payload_str)
            except Exception:
                st.session_state.mqtt_broker_available = False
                status = "📡 Simulated"
                st.session_state.mqtt_mock_queue.append(
                    {"topic": topic, "payload": payload_str, "timestamp": timestamp}
                )
        else:
            status = "📡 Simulated"
            st.session_state.mqtt_mock_queue.append(
                {"topic": topic, "payload": payload_str, "timestamp": timestamp}
            )

        new_entries.append(
            {
                "Timestamp": timestamp,
                "Topic": topic,
                "Payload": payload_str,
                "Status": status,
            }
        )

    st.session_state.mqtt_feed = (st.session_state.mqtt_feed + new_entries)[-10:]
    st.session_state.mqtt_last_sync = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    broker_label = "Mosquitto (local)" if st.session_state.mqtt_broker_available else "Mock queue (session_state)"
    return broker_label
