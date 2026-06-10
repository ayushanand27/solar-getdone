import json
import ssl
import threading
import time
from datetime import datetime

import paho.mqtt.client as mqtt
import streamlit as st


def _create_mqtt_client(client_id):
    kwargs = {
        "client_id": client_id,
        "protocol": mqtt.MQTTv311,
    }
    if hasattr(mqtt, "CallbackAPIVersion"):
        kwargs["callback_api_version"] = mqtt.CallbackAPIVersion.VERSION1
    return mqtt.Client(**kwargs)


def publish_if_due(solar_output, temp, wind, shield, mode, threat):
    if "last_mqtt" not in st.session_state:
        st.session_state.last_mqtt = 0

    current_time = time.time()
    if current_time - st.session_state.last_mqtt > 60:
        success, msg = publish_to_hivemq(solar_output, temp, wind, shield, mode, threat)
        st.session_state.last_mqtt = current_time
        st.session_state.last_mqtt_result = (success, msg)
        return success, msg

    return st.session_state.get("last_mqtt_result", (False, "Waiting for next publish window"))


def publish_to_hivemq(solar_output, temp, wind, shield, mode, threat):
    result = {"success": False, "msg": "Not started"}
    published_count = [0]

    messages = {
        "solar/weather": {
            "temp": temp,
            "wind": wind,
            "location": st.session_state.get("city_name", "Unknown"),
            "ts": datetime.now().isoformat(),
        },
        "solar/shield": {
            "status": shield,
            "ts": datetime.now().isoformat(),
        },
        "solar/energy_mode": {
            "mode": mode,
            "solar_output": solar_output,
            "ts": datetime.now().isoformat(),
        },
        "solar/alerts": {
            "level": threat,
            "ts": datetime.now().isoformat(),
        },
    }

    def _run():
        client = None
        try:
            host = st.secrets["mqtt"]["host"]
            port = 8883
            username = st.secrets["mqtt"]["username"]
            password = st.secrets["mqtt"]["password"]

            client = _create_mqtt_client(f"solar-os-{int(time.time())}")
            client.username_pw_set(username, password)
            client.tls_set(tls_version=ssl.PROTOCOL_TLS)

            connected = threading.Event()

            def on_connect(c, userdata, flags, rc):
                if rc == 0:
                    connected.set()

            client.on_connect = on_connect
            client.connect(host, port, keepalive=60)
            client.loop_start()

            if not connected.wait(timeout=5):
                result["msg"] = "Connection timeout"
                return

            for topic, payload in messages.items():
                retain = topic == "solar/weather"
                info = client.publish(
                    topic,
                    json.dumps(payload),
                    qos=1,
                    retain=retain,
                )
                info.wait_for_publish(timeout=3)
                published_count[0] += 1

            time.sleep(1)
            result["success"] = True
            result["msg"] = f"Published {published_count[0]} messages"
        except Exception as e:
            result["msg"] = str(e)
        finally:
            if client is not None:
                try:
                    client.loop_stop()
                    client.disconnect()
                except Exception:
                    pass

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=10)

    return result["success"], result["msg"]
