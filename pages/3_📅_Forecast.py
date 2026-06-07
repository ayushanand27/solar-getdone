import streamlit as st
st.set_page_config(page_title="Solar OS", layout="wide", page_icon="☀️")

from datetime import datetime

import pandas as pd

from utils.app_state import setup_app

ctx = setup_app()

st.title("📅 Forecast & Alerts")
st.caption(f"7-day AI plan and real-time alerts | 📍 {ctx['city_name']}")

st.subheader("📅 7-Day Solar Forecast + AI Plan")
days = ctx["forecast"]["daily"]
day_rows = []
for i in range(7):
    wc = days["weathercode"][i]
    rad = days["shortwave_radiation_sum"][i]
    prec = days["precipitation_sum"][i]
    wind_max = days["windspeed_10m_max"][i]
    date = days["time"][i]
    est_output = round(rad * 0.22, 1) if rad else 0
    if wc >= 95:
        ai_plan, rec = "🛡️ Shield closed all day", "🔴 Storm — protect panels"
    elif wc >= 61 or prec > 2:
        ai_plan, rec = "🛡️ Shield closed — rain", "🟠 Rain — minimal harvest"
    elif est_output > 3000:
        ai_plan, rec = "⚡ Full harvest + H₂ store", "🟢 Excellent day — max production"
    elif est_output > 1000:
        ai_plan, rec = "🔋 Normal harvest + store", "🟡 Good day — normal ops"
    else:
        ai_plan, rec = "🌙 Distribute stored energy", "⚪ Low solar — use reserves"
    day_rows.append(
        {
            "Date": date,
            "Est. Output (Wh/m²)": est_output,
            "Rain (mm)": prec,
            "Max Wind (km/h)": wind_max,
            "AI Plan": ai_plan,
            "Status": rec,
        }
    )

day_df = pd.DataFrame(day_rows)
st.dataframe(day_df, use_container_width=True, hide_index=True)
best_day = day_df.loc[day_df["Est. Output (Wh/m²)"].idxmax(), "Date"]
worst_day = day_df.loc[day_df["Est. Output (Wh/m²)"].idxmin(), "Date"]
storm_days = day_df[day_df["Rain (mm)"] > 2].shape[0]
st.info(
    f"🤖 **AI Weekly Insight:** Best day → **{best_day}** | "
    f"Storm days → **{storm_days}** | Low day → **{worst_day}** — pre-charge batteries!"
)

st.divider()
st.subheader("🚨 Real-Time Alert System")
alerts = []
if ctx["wcode"] >= 95:
    alerts.append(("CRITICAL", "⛈️ THUNDERSTORM", f"Shield closed. Location: {ctx['city_name']}"))
if ctx["wcode"] >= 61 or ctx["rain"] > 0.5:
    alerts.append(("HIGH", "🌧️ HEAVY RAINFALL", f"Rain: {ctx['rain']}mm. Panels protected."))
if ctx["wind"] > 60:
    alerts.append(("HIGH", "💨 EXTREME WIND", f"{ctx['wind']} km/h — shield closed."))
if ctx["wind"] > 40:
    alerts.append(("MEDIUM", "⚠️ HIGH WIND", f"{ctx['wind']} km/h — standby."))
if ctx["solar_output"] < 10 and 7 < datetime.now().hour < 17:
    alerts.append(("MEDIUM", "☁️ LOW SOLAR", f"Only {ctx['solar_output']} W/m² during daylight."))
if ctx["sim_event"] == "bird":
    alerts.append(("HIGH", "🐦 BIRD DETECTED", "Deterrent active. Shield partially closing."))
if ctx["sim_event"] == "dust":
    alerts.append(("HIGH", "🌫️ DUST STORM", "25% efficiency drop. Auto-clean initiated."))
for row in day_rows:
    if "Storm" in row["Status"] or "Rain" in row["Status"]:
        alerts.append(("LOW", f"📅 UPCOMING: {row['Date']}", f"{row['AI Plan']} — Pre-charge batteries."))

if not alerts:
    st.success("✅ All systems normal — No active alerts")
else:
    for level, title, msg in alerts:
        if level == "CRITICAL":
            st.error(f"🔴 **{title}**\n\n{msg}")
        elif level == "HIGH":
            st.error(f"🟠 **{title}**\n\n{msg}")
        elif level == "MEDIUM":
            st.warning(f"🟡 **{title}**\n\n{msg}")
        else:
            st.info(f"🔵 **{title}**\n\n{msg}")
st.caption(f"Last checked: {datetime.now().strftime('%H:%M:%S')} | {ctx['city_name']}")
