import json
import ssl
import time
from datetime import datetime

import paho.mqtt.client as mqtt
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
    try:
        host = st.secrets["mqtt"]["host"]
        port = int(st.secrets["mqtt"]["port"])
        username = st.secrets["mqtt"]["username"]
        password = st.secrets["mqtt"]["password"]

        messages = {
            "solar/weather": {
                "temp": temp,
                "wind": wind,
                "timestamp": datetime.now().isoformat(),
            },
            "solar/shield": {
                "status": shield,
                "timestamp": datetime.now().isoformat(),
            },
            "solar/energy_mode": {
                "mode": mode,
                "solar_output": solar_output,
                "timestamp": datetime.now().isoformat(),
            },
            "solar/alerts": {
                "level": threat,
                "timestamp": datetime.now().isoformat(),
            },
        }

        published = []

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                for topic, payload in messages.items():
                    client.publish(topic, json.dumps(payload), qos=0)
                    published.append(topic)

        def on_publish(client, userdata, mid):
            if len(published) >= len(messages):
                client.disconnect()

        client = mqtt.Client(
            client_id=f"solar-os-{int(time.time())}",
            protocol=mqtt.MQTTv311,
        )
        client.username_pw_set(username, password)
        client.tls_set(tls_version=ssl.PROTOCOL_TLS)
        client.on_connect = on_connect
        client.on_publish = on_publish

        client.connect(host, port, keepalive=10)
        client.loop_start()
        time.sleep(2)
        client.loop_stop()
        client.disconnect()

        return True, "Connected"

    except Exception as e:
        return False, str(e)
