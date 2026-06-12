import streamlit as st

st.set_page_config(page_title="Solar OS", layout="wide", page_icon="☀️")

from utils.ai_engine import apply_sim_overrides
from utils.app_state import setup_app

ctx = setup_app()

sim_event = ctx["sim_event"]
if ctx.get("cv_threat") in ("bird", "dust"):
    sim_event = ctx["cv_threat"]
    st.session_state.sim_event = sim_event

if ctx["shield"] != "CLOSED":
    status, action, mode, solar_output, shield, shield_reason, threat_level = apply_sim_overrides(
        sim_event,
        ctx["status"],
        ctx["action"],
        ctx["mode"],
        ctx["solar_output"],
        ctx["shield"],
        ctx["shield_reason"],
        ctx["threat_level"],
        ctx["radiation"],
        ctx.get("hours"),
    )
else:
    status, action, mode, solar_output, shield, shield_reason, threat_level = (
        ctx["status"],
        ctx["action"],
        ctx["mode"],
        ctx["solar_output"],
        ctx["shield"],
        ctx["shield_reason"],
        ctx["threat_level"],
    )

st.session_state.shield_status = shield
ctx.update(
    {
        "sim_event": sim_event,
        "status": status,
        "action": action,
        "mode": mode,
        "solar_output": solar_output,
        "shield": shield,
        "shield_reason": shield_reason,
        "threat_level": threat_level,
    }
)

st.title("🛡️ Shield Protection")
st.caption(f"Autonomous panel protection | 📍 {ctx['city_name']}")

if ctx.get("auto_sim"):
    cycle_labels = {None: "✅ Clear skies", "bird": "🐦 Bird attack", "dust": "🌫️ Dust storm"}
    st.info(
        f"⚡ **Auto simulation active** — current cycle: **{cycle_labels.get(sim_event, sim_event)}** "
        "(refreshes every 5 seconds)"
    )

if sim_event == "bird":
    st.warning("🐦 **Bird threat active** — shield on standby with partial closure.")
elif sim_event == "dust":
    st.warning("🌫️ **Dust storm active** — 25% panel efficiency loss. Auto-clean sequence running.")

st.subheader("🛡️ Shield Protection System")
s1, s2, s3 = st.columns(3)
with s1:
    if ctx["shield"] == "CLOSED":
        st.error(f"### 🔒 SHIELD: CLOSED\n**Reason:** {ctx['shield_reason']}\n\nPanels fully protected.")
    elif ctx["shield"] == "READY":
        shield_label = "STANDBY / PARTIAL" if sim_event == "bird" else "STANDBY"
        st.warning(f"### ⚠️ SHIELD: {shield_label}\n**Reason:** {ctx['shield_reason']}\n\nShield ready to deploy.")
    else:
        st.success(f"### ✅ SHIELD: OPEN\n**Reason:** {ctx['shield_reason']}\n\nMaximum harvesting active.")

with s2:
    st.markdown("### 🎯 Threat Assessment")
    if ctx["threat_level"] == "CRITICAL":
        st.error("🔴 CRITICAL THREAT")
        st.progress(100)
    elif ctx["threat_level"] == "HIGH":
        st.error("🟠 HIGH THREAT")
        st.progress(75)
    elif ctx["threat_level"] == "MEDIUM":
        st.warning("🟡 MEDIUM THREAT")
        st.progress(50)
    else:
        st.success("🟢 LOW THREAT")
        st.progress(15)
    st.caption(f"Weather code: {ctx['wcode']} | Wind: {ctx['wind']} km/h | Rain: {ctx['rain']}mm")

with s3:
    st.markdown("### 📋 Threat Breakdown")
    threats = {
        "⛈️ Thunderstorm": "🔴 YES" if ctx["wcode"] >= 95 else "🟢 NO",
        "🌧️ Heavy Rain": "🔴 YES" if ctx["rain"] > 0.5 else "🟢 NO",
        "💨 Extreme Wind": "🔴 YES" if ctx["wind"] > 60 else "🟢 NO",
        "⚠️ High Wind": "🟡 WATCH" if 40 < ctx["wind"] <= 60 else "🟢 NO",
        "🌫️ Dust Storm": "🔴 YES" if sim_event == "dust" else "🟢 NO",
        "🐦 Bird Activity": "🔴 YES" if sim_event == "bird" else "🟢 NO",
    }
    for label, value in threats.items():
        st.markdown(f"{label} — **{value}**")
st.divider()

st.subheader("🔬 CV Threat Detection Module")
cv_col1, cv_col2 = st.columns([2, 1])
with cv_col1:
    if ctx["cv_display_image"] is not None:
        st.image(ctx["cv_display_image"], caption=f"Analyzing: {ctx['cv_filename']}", use_container_width=True)
    else:
        st.info("Use the **🔬 CV Detection** sidebar to select a sample image or upload your own.")
with cv_col2:
    st.markdown("### 🎯 Detection Result")
    if ctx["cv_threat"]:
        threat_labels = {"bird": "🐦 Bird / Animal", "dust": "🌫️ Dust / Haze", "damage": "💥 Panel Damage"}
        label = threat_labels.get(ctx["cv_threat"], ctx["cv_threat"].title())
        st.markdown(f"**Threat Type:** {label}")
        st.markdown(f"**Confidence:** {ctx['cv_confidence']:.0%}" if ctx["cv_confidence"] else "**Confidence:** —")
        if ctx["cv_detections"] and ctx["cv_source"] == "📤 Upload My Image":
            st.caption("YOLOv8n detections:")
            for det in ctx["cv_detections"][:5]:
                st.caption(f"• {det['class']} ({det['confidence']:.0%})")
    else:
        st.markdown("**Threat Type:** None detected")
        st.markdown("**Confidence:** —")
        if ctx["cv_detections"] and ctx["cv_source"] == "📤 Upload My Image":
            st.caption("YOLOv8n detections:")
            for det in ctx["cv_detections"][:5]:
                st.caption(f"• {det['class']} ({det['confidence']:.0%})")

    st.markdown("### ⚖️ Threat Verdict")
    if ctx["cv_verdict"] == "HIGH":
        st.error(f"**{ctx['cv_verdict']}** — {ctx['cv_explanation']}")
    elif ctx["cv_verdict"] == "MEDIUM":
        st.warning(f"**{ctx['cv_verdict']}** — {ctx['cv_explanation']}")
    else:
        st.success(f"**{ctx['cv_verdict']}** — {ctx['cv_explanation']}")

if ctx["cv_threat"] == "damage":
    st.error(
        "🚨 **Panel Damage Alert** — CV detected cracked/damaged solar panels. "
        "Schedule immediate inspection and panel replacement."
    )
