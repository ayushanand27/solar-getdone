import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import streamlit as st

from utils.weather import IST


def _normalize_gmail_password(password):
    """Gmail app passwords work with or without spaces — normalize for SMTP login."""
    return password.replace(" ", "") if password else password


def send_email_alert(alert_type, message, to_email):
    try:
        sender = st.secrets["email"]["sender"]
        password = _normalize_gmail_password(st.secrets["email"]["password"])

        if not to_email or not str(to_email).strip():
            return False, "No recipient email address"

        to_email = str(to_email).strip()

        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = to_email
        msg["Subject"] = f"Solar OS Alert: {alert_type}"

        city = st.session_state.get("city_name", "Unknown")
        body = f"""Solar OS - Autonomous Farm Alert

Alert Type: {alert_type}
Message: {message}
Time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')}
Location: {city}

Dashboard: https://solar-os-ai.streamlit.app
"""
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(sender, password)
            server.sendmail(sender, to_email, msg.as_string())

        return True, "Email sent successfully"

    except smtplib.SMTPAuthenticationError:
        return False, "Gmail auth failed — check App Password in secrets"
    except smtplib.SMTPException as exc:
        return False, f"SMTP error: {exc}"
    except KeyError as exc:
        return False, f"Missing secret: {exc}"
    except Exception as exc:
        return False, f"Error: {exc}"
