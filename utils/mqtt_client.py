import threading
import time

import streamlit as st


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
    import json
    import ssl
    from datetime import datetime

    import paho.mqtt.client as mqtt

    result = {"success": False, "msg": "Timeout"}

    messages = {
        "solar/weather": {"temp": temp, "wind": wind, "ts": datetime.now().isoformat()},
        "solar/shield": {"status": shield, "ts": datetime.now().isoformat()},
        "solar/energy_mode": {"mode": mode, "solar": solar_output, "ts": datetime.now().isoformat()},
        "solar/alerts": {"level": threat, "ts": datetime.now().isoformat()},
    }

    def _publish():
        try:
            host = st.secrets["mqtt"]["host"]
            port = 8883
            username = st.secrets["mqtt"]["username"]
            password = st.secrets["mqtt"]["password"]

            c = mqtt.Client(client_id=f"solar-{int(time.time())}", protocol=mqtt.MQTTv311)
            c.username_pw_set(username, password)
            c.tls_set(tls_version=ssl.PROTOCOL_TLS)
            c.connect(host, port, keepalive=30)
            c.loop_start()
            time.sleep(1.5)
            for topic, payload in messages.items():
                c.publish(topic, json.dumps(payload), qos=0)
            time.sleep(1.5)
            c.loop_stop()
            c.disconnect()
            result["success"] = True
            result["msg"] = "Published"
        except Exception as e:
            result["msg"] = str(e)

    t = threading.Thread(target=_publish, daemon=True)
    t.start()
    t.join(timeout=8)

    return result["success"], result["msg"]
