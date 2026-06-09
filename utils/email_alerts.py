import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import streamlit as st


def send_email_alert(alert_type, message, to_email):
    sender = st.secrets["email"]["sender"]
    password = st.secrets["email"]["password"]

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = f"☀️ Solar OS Alert: {alert_type}"

    body = f"""
Solar OS — Autonomous Farm Alert

Alert Type: {alert_type}
Message: {message}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Dashboard: localhost:8501
"""
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, to_email, msg.as_string())
