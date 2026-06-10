from datetime import datetime
from io import BytesIO

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

GREEN = colors.HexColor("#00C896")
RED = colors.HexColor("#EF4444")
YELLOW = colors.HexColor("#F7B731")
DARK = colors.HexColor("#0D1117")
GREY = colors.HexColor("#8B949E")

STATUS_OPTIONS = ["✅ Compliant", "⚠️ Partial", "❌ Non-Compliant"]

CHECKLIST = [
    {
        "category": "PANEL STANDARDS",
        "items": [
            {"id": "bypass_diodes", "label": "Bypass diodes installed (mandatory 2027)", "default": "✅ Compliant"},
            {"id": "rfid_tags", "label": "RFID tracking tags on all modules", "default": "⚠️ Partial"},
            {"id": "lifespan_25yr", "label": "Designed for 25-year minimum lifespan", "default": "✅ Compliant"},
            {"id": "anti_soiling", "label": "Anti-soiling coating present", "default": "⚠️ Partial"},
            {"id": "hail_iec61215", "label": "Hail resistance rating IEC 61215", "default": "✅ Compliant"},
        ],
    },
    {
        "category": "BESS (Battery Energy Storage)",
        "items": [
            {"id": "bms_active", "label": "Battery Management System (BMS) active", "default": "✅ Compliant"},
            {"id": "thermal_runaway", "label": "Thermal runaway protection enabled", "default": "✅ Compliant"},
            {"id": "soc_monitoring", "label": "State of Charge monitoring (<90% max)", "default": "⚠️ Partial"},
            {"id": "grid_disconnect", "label": "Grid disconnection relay tested", "default": "✅ Compliant"},
            {"id": "fire_suppression", "label": "Fire suppression system linked", "default": "❌ Non-Compliant"},
        ],
    },
    {
        "category": "MONITORING & SAFETY",
        "items": [
            {"id": "rt_monitoring", "label": "Real-time output monitoring active", "default": "✅ Compliant"},
            {"id": "fault_detection", "label": "Fault detection system operational", "default": "✅ Compliant"},
            {"id": "lightning_arrestor", "label": "Lightning arrestor installed", "default": "✅ Compliant"},
            {"id": "earth_fault", "label": "Earth fault protection active", "default": "⚠️ Partial"},
            {"id": "emergency_shutdown", "label": "Emergency shutdown tested", "default": "✅ Compliant"},
        ],
    },
    {
        "category": "REPORTING & DOCUMENTATION",
        "items": [
            {"id": "monthly_logs", "label": "Monthly generation logs maintained", "default": "✅ Compliant"},
            {"id": "maintenance_records", "label": "Maintenance records updated", "default": "⚠️ Partial"},
            {"id": "grid_approval", "label": "Grid injection approval obtained", "default": "✅ Compliant"},
            {"id": "env_clearance", "label": "Environmental clearance active", "default": "✅ Compliant"},
            {"id": "insurance", "label": "Insurance coverage valid", "default": "❌ Non-Compliant"},
        ],
    },
]

ACTIONS = {
    "bypass_diodes": "Verify bypass diode continuity on all strings before April 2027.",
    "rfid_tags": "Install RFID tags on remaining untagged modules and update asset registry.",
    "lifespan_25yr": "Submit manufacturer lifespan certificates for all panel batches.",
    "anti_soiling": "Apply anti-soiling coating to uncovered arrays; schedule quarterly inspection.",
    "hail_iec61215": "Obtain IEC 61215 hail test certification for installed module models.",
    "bms_active": "Commission BMS firmware audit and enable remote monitoring alerts.",
    "thermal_runaway": "Test thermal runaway sensors and validate automatic shutdown triggers.",
    "soc_monitoring": "Calibrate SOC sensors and enforce 90% maximum charge policy.",
    "grid_disconnect": "Perform annual grid disconnection relay test and log results.",
    "fire_suppression": "Link BESS fire suppression to central alarm and conduct drill.",
    "rt_monitoring": "Enable continuous SCADA output monitoring with 15-minute logging.",
    "fault_detection": "Run fault detection self-test and repair flagged inverter channels.",
    "lightning_arrestor": "Inspect lightning arrestor grounding resistance (<10Ω required).",
    "earth_fault": "Upgrade earth fault protection relays on feeder lines.",
    "emergency_shutdown": "Conduct emergency shutdown drill and document response time.",
    "monthly_logs": "Archive monthly generation logs in CEA-compliant format.",
    "maintenance_records": "Update maintenance records for Q1–Q2 2026 inspections.",
    "grid_approval": "Renew grid injection approval with state DISCOM.",
    "env_clearance": "Renew environmental clearance before expiry date.",
    "insurance": "Renew farm insurance policy covering equipment and liability.",
}


def all_items():
    items = []
    for category in CHECKLIST:
        for item in category["items"]:
            items.append({**item, "category": category["category"]})
    return items


def init_compliance_state():
    if "cea_compliance" not in st.session_state:
        st.session_state.cea_compliance = {
            item["id"]: item["default"] for item in all_items()
        }


def calculate_score(statuses):
    weights = {"✅ Compliant": 1.0, "⚠️ Partial": 0.5, "❌ Non-Compliant": 0.0}
    items = all_items()
    if not items:
        return 0
    total = sum(weights.get(statuses.get(item["id"], item["default"]), 0) for item in items)
    return round((total / len(items)) * 100)


def compliance_grade(score):
    if score >= 80:
        return "🟢 Compliant", "#00C896"
    if score >= 50:
        return "🟡 Partial", "#F7B731"
    return "🔴 Non-Compliant", "#EF4444"


def row_style(status):
    if status == "✅ Compliant":
        return "background:#0D2818;border-left:4px solid #00C896;"
    if status == "⚠️ Partial":
        return "background:#2A2208;border-left:4px solid #F7B731;"
    return "background:#2A1010;border-left:4px solid #EF4444;"


def get_alerts(statuses):
    alerts = []
    for item in all_items():
        status = statuses.get(item["id"], item["default"])
        if status in ("⚠️ Partial", "❌ Non-Compliant"):
            alerts.append(
                {
                    "label": item["label"],
                    "status": status,
                    "action": ACTIONS.get(item["id"], "Review and remediate before deadline."),
                    "category": item["category"],
                }
            )
    return alerts


def generate_compliance_pdf(farm_name, score, grade_label, statuses, report_date):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], alignment=TA_CENTER, textColor=DARK, fontSize=22)
    sub_style = ParagraphStyle("Sub", parent=styles["Normal"], alignment=TA_CENTER, textColor=GREY, fontSize=11)
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14)

    story = [
        Paragraph("CEA 2026 Compliance Report", title_style),
        Spacer(1, 0.15 * inch),
        Paragraph(f"Farm: <b>{farm_name}</b>", sub_style),
        Paragraph(f"Date: {report_date}", sub_style),
        Paragraph("Central Electricity Authority — Amendment 2026", sub_style),
        Spacer(1, 0.3 * inch),
        Paragraph(f"<b>Compliance Score:</b> {score}/100 — {grade_label}", body),
        Spacer(1, 0.25 * inch),
    ]

    for category in CHECKLIST:
        story.append(Paragraph(f"<b>{category['category']}</b>", body))
        story.append(Spacer(1, 0.1 * inch))
        rows = [["Item", "Status"]]
        for item in category["items"]:
            rows.append([item["label"], statuses.get(item["id"], item["default"])])
        table = Table(rows, colWidths=[4.2 * inch, 1.8 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), DARK),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))

    alerts = get_alerts(statuses)
    story.append(Paragraph("<b>Action Items</b>", body))
    story.append(Spacer(1, 0.1 * inch))
    if alerts:
        for alert in alerts:
            story.append(
                Paragraph(
                    f"• [{alert['status']}] {alert['label']}<br/>"
                    f"&nbsp;&nbsp;Action Required: {alert['action']}<br/>"
                    f"&nbsp;&nbsp;Deadline: April 1, 2027",
                    body,
                )
            )
            story.append(Spacer(1, 0.08 * inch))
    else:
        story.append(Paragraph("No open action items — fully compliant.", body))

    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph("<i>Generated by Solar OS — CEA 2026 Compliance Module</i>", sub_style))

    doc.build(story)
    return buffer.getvalue()
