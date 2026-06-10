import streamlit as st

st.set_page_config(page_title="Solar OS", layout="wide", page_icon="☀️")

from datetime import datetime

import plotly.graph_objects as go

from utils.app_state import setup_app
from utils.compliance_report import (
    CHECKLIST,
    STATUS_OPTIONS,
    calculate_score,
    compliance_grade,
    generate_compliance_pdf,
    get_alerts,
    init_compliance_state,
    row_style,
)

ctx = setup_app()
init_compliance_state()

statuses = st.session_state.cea_compliance
report_date = datetime.now().strftime("%Y-%m-%d")

st.title("📋 CEA 2026 Compliance Dashboard")
st.caption(
    "Central Electricity Authority Technical Standards Amendment 2026 — Effective April 2027"
)

st.info(
    "CEA Technical Standards Amendment 2026 mandates new safety and quality benchmarks "
    "for all solar installations above 1MW in India, effective April 1, 2027."
)

score_slot = st.empty()

st.divider()
st.subheader("✅ Compliance Checklist")

for category in CHECKLIST:
    st.markdown(f"### {category['category']}")
    for item in category["items"]:
        c1, c2 = st.columns([3, 1])
        current = statuses.get(item["id"], item["default"])
        with c1:
            st.markdown(
                f'<div style="{row_style(current)}padding:12px 16px;border-radius:8px;margin-bottom:8px;">'
                f'<span style="color:#E6EDF3;">{item["label"]}</span></div>',
                unsafe_allow_html=True,
            )
        with c2:
            selected = st.selectbox(
                "Status",
                STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(current),
                key=f"cea_{item['id']}",
                label_visibility="collapsed",
            )
            statuses[item["id"]] = selected
    st.markdown("")

st.session_state.cea_compliance = statuses
score = calculate_score(statuses)
grade_label, grade_color = compliance_grade(score)
compliant_count = sum(1 for v in statuses.values() if v == "✅ Compliant")
partial_count = sum(1 for v in statuses.values() if v == "⚠️ Partial")
non_count = sum(1 for v in statuses.values() if v == "❌ Non-Compliant")

with score_slot.container():
    score_col, gauge_col = st.columns([1, 2])
    with score_col:
        st.metric("Compliance Score", f"{score}/100", grade_label)
        st.markdown(
            f"✅ **{compliant_count}** Compliant · "
            f"⚠️ **{partial_count}** Partial · "
            f"❌ **{non_count}** Non-Compliant"
        )
    with gauge_col:
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=score,
                number={"suffix": "/100", "font": {"size": 42, "color": "#E6EDF3"}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "#8B949E"},
                    "bar": {"color": grade_color},
                    "bgcolor": "#161B22",
                    "borderwidth": 0,
                    "steps": [
                        {"range": [0, 50], "color": "#2A1010"},
                        {"range": [50, 80], "color": "#2A2208"},
                        {"range": [80, 100], "color": "#0D2818"},
                    ],
                },
                title={"text": grade_label, "font": {"size": 18, "color": grade_color}},
            )
        )
        fig.update_layout(
            height=280,
            margin=dict(l=30, r=30, t=60, b=20),
            paper_bgcolor="#0D1117",
            plot_bgcolor="#0D1117",
            font=dict(color="#E6EDF3"),
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("⚠️ Non-Compliance Alerts")

alerts = get_alerts(statuses)
if alerts:
    for alert in alerts:
        if alert["status"] == "❌ Non-Compliant":
            st.error(
                f"**{alert['label']}** ({alert['category']})\n\n"
                f"Action Required: {alert['action']}\n\n"
                f"Deadline: **Required by April 1, 2027**"
            )
        else:
            st.warning(
                f"**{alert['label']}** ({alert['category']})\n\n"
                f"Action Required: {alert['action']}\n\n"
                f"Deadline: **Required by April 1, 2027**"
            )
else:
    st.success("All checklist items are fully compliant. No action items pending.")

st.divider()
city_slug = ctx["city_name"].replace(" ", "_")
pdf_bytes = generate_compliance_pdf(ctx["city_name"], score, grade_label, statuses, report_date)
st.download_button(
    label="📄 Export Compliance Report",
    data=pdf_bytes,
    file_name=f"SolarOS_CEA_Compliance_{city_slug}_{report_date}.pdf",
    mime="application/pdf",
    use_container_width=True,
)
