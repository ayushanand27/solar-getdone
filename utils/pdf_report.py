from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Brand palette
SOLAR_YELLOW = colors.HexColor("#F7B731")
DARK_BG = colors.HexColor("#0D1117")
GREEN = colors.HexColor("#00C896")
RED = colors.HexColor("#EF4444")
TEXT_DARK = colors.HexColor("#1a1a1a")
BLUE = colors.HexColor("#3B82F6")
PURPLE = colors.HexColor("#8B5CF6")
TEAL = colors.HexColor("#14B8A6")
LIGHT_GREEN = colors.HexColor("#E8FBF5")
LIGHT_RED = colors.HexColor("#FEECEC")
LIGHT_GREY = colors.HexColor("#F4F4F5")
WHITE = colors.white


def compute_analytics_metrics(ctx, farm_size, electricity_rate, diesel_rate):
    daily_hours = sum(1 for r in ctx["radiation"] if r * 0.22 > 50)
    daily_energy_kwh = round(farm_size * daily_hours * 0.22, 1)
    annual_energy_kwh = round(daily_energy_kwh * 365, 1)
    annual_savings_inr = round(annual_energy_kwh * electricity_rate, 0)
    diesel_displaced_litres = round(annual_energy_kwh / 3.5, 1)
    co2_saved_kg = round(annual_energy_kwh * 0.82, 1)
    h2_kg = round(sum(r * 0.22 * 0.7 for r in ctx["radiation"] if r > 100) / 1000, 2)
    battery_level = min(100, int(ctx["solar_output"] / 2))
    h2_level = min(100, int(h2_kg * 40))
    return {
        "farm_size": farm_size,
        "electricity_rate": electricity_rate,
        "diesel_rate": diesel_rate,
        "daily_hours": daily_hours,
        "daily_energy_kwh": daily_energy_kwh,
        "annual_energy_kwh": annual_energy_kwh,
        "annual_savings_inr": annual_savings_inr,
        "diesel_displaced_litres": diesel_displaced_litres,
        "co2_saved_kg": co2_saved_kg,
        "h2_kg": h2_kg,
        "battery_level": battery_level,
        "h2_level": h2_level,
    }


def build_forecast_rows(ctx):
    days = ctx["forecast"]["daily"]
    rows = []
    for i in range(7):
        wc = days["weathercode"][i]
        rad = days["shortwave_radiation_sum"][i]
        prec = days["precipitation_sum"][i]
        date = days["time"][i]
        est_output = round(rad * 0.22, 1) if rad else 0
        if wc >= 95:
            ai_plan, rec = "Shield closed all day", "Storm - protect panels"
            row_type = "rain"
        elif wc >= 61 or prec > 2:
            ai_plan, rec = "Shield closed - rain", "Rain - minimal harvest"
            row_type = "rain"
        elif est_output > 3000:
            ai_plan, rec = "Full harvest + H2 store", "Excellent day"
            row_type = "good"
        elif est_output > 1000:
            ai_plan, rec = "Normal harvest + store", "Good day"
            row_type = "good"
        else:
            ai_plan, rec = "Distribute stored energy", "Low solar"
            row_type = "neutral"
        rows.append(
            {
                "Date": date,
                "Est Output": est_output,
                "Rain": prec,
                "AI Plan": ai_plan,
                "Status": rec,
                "row_type": row_type,
            }
        )
    return rows


def build_recommendations(ctx, metrics):
    recs = []
    if ctx["sim_event"] == "dust" or ctx["temp"] > 35:
        recs.append("High dust season — schedule panel cleaning every 3 days.")
    elif ctx["wcode"] >= 61:
        recs.append("Rain expected — keep shields on standby and defer grid export.")

    hour = datetime.now().hour
    if hour in {6, 7, 8, 9, 18, 19, 20, 21}:
        recs.append("Peak pricing window 6-10am / 6-10pm — export surplus now.")
    elif ctx["solar_output"] > 50:
        recs.append("Moderate solar window — prioritize battery charge then H2 conversion.")

    h2_level = metrics["h2_level"]
    if h2_level > 80:
        recs.append(f"H2 tank at {h2_level}% — redirect surplus to grid export.")
    else:
        recs.append(f"H2 tank at {h2_level}% — continue electrolysis mode.")

    if ctx["threat_level"] in ("HIGH", "CRITICAL"):
        recs.insert(0, f"Threat level {ctx['threat_level']} — review shield logs and farm cameras.")

    while len(recs) < 3:
        recs.append("Maintain normal harvest/store cycle — all core systems within range.")

    return recs[:3]


def _build_styles():
    base = getSampleStyleSheet()
    base.add(
        ParagraphStyle(
            name="CoverReportTitle",
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=TEXT_DARK,
            spaceAfter=16,
            alignment=TA_LEFT,
        )
    )
    base.add(
        ParagraphStyle(
            name="CoverFooter",
            fontName="Helvetica-Oblique",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#666666"),
            alignment=TA_CENTER,
        )
    )
    base.add(
        ParagraphStyle(
            name="SectionHeader",
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=TEXT_DARK,
            leftIndent=12,
            spaceBefore=4,
            spaceAfter=14,
        )
    )
    base.add(
        ParagraphStyle(
            name="CardValue",
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=WHITE,
            alignment=TA_CENTER,
        )
    )
    base.add(
        ParagraphStyle(
            name="CardLabel",
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=WHITE,
            alignment=TA_CENTER,
        )
    )
    base.add(
        ParagraphStyle(
            name="CardIcon",
            fontName="Helvetica",
            fontSize=14,
            leading=16,
            textColor=WHITE,
            alignment=TA_CENTER,
        )
    )
    base.add(
        ParagraphStyle(
            name="BadgeText",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=WHITE,
            alignment=TA_CENTER,
        )
    )
    base.add(
        ParagraphStyle(
            name="HighlightBox",
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            textColor=TEXT_DARK,
        )
    )
    base.add(
        ParagraphStyle(
            name="RecNumber",
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=SOLAR_YELLOW,
        )
    )
    base.add(
        ParagraphStyle(
            name="RecBody",
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            textColor=TEXT_DARK,
        )
    )
    base.add(
        ParagraphStyle(
            name="EnergyValueGreen",
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=GREEN,
            alignment=TA_CENTER,
        )
    )
    base.add(
        ParagraphStyle(
            name="EnergyValueYellow",
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=SOLAR_YELLOW,
            alignment=TA_CENTER,
        )
    )
    base.add(
        ParagraphStyle(
            name="EnergyLabel",
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=TEXT_DARK,
            alignment=TA_CENTER,
        )
    )
    return base


def _draw_cover_header(canvas, doc):
    canvas.saveState()
    page_w, page_h = A4
    canvas.setFillColor(SOLAR_YELLOW)
    canvas.rect(0, page_h - 2 * inch, page_w, 2 * inch, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 30)
    canvas.drawCentredString(page_w / 2, page_h - 1.2 * inch, "☀ SOLAR OS")
    canvas.restoreState()


def _section_header(title, styles):
    bar = Table(
        [[None, Paragraph(title, styles["SectionHeader"])]],
        colWidths=[0.12 * inch, 6.3 * inch],
    )
    bar.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), SOLAR_YELLOW),
                ("BACKGROUND", (1, 0), (1, 0), LIGHT_GREY),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (1, 0), (1, 0), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return bar


def _metric_card(icon, value, label, bg_color, styles):
    card = Table(
        [
            [Paragraph(icon, styles["CardIcon"])],
            [Paragraph(value, styles["CardValue"])],
            [Paragraph(label, styles["CardLabel"])],
        ],
        colWidths=[2.95 * inch],
    )
    card.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg_color),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("ROUNDEDCORNERS", [8, 8, 8, 8]),
            ]
        )
    )
    return card


def _status_badge(text, bg_color, styles):
    badge = Table([[Paragraph(text, styles["BadgeText"])]], colWidths=[2.8 * inch])
    badge.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg_color),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("ROUNDEDCORNERS", [6, 6, 6, 6]),
            ]
        )
    )
    return badge


def _shield_badge(shield):
    if shield == "CLOSED":
        return RED
    if shield == "READY":
        return SOLAR_YELLOW
    return GREEN


def _threat_badge_color(threat_level):
    if threat_level in ("CRITICAL", "HIGH"):
        return RED
    if threat_level == "MEDIUM":
        return SOLAR_YELLOW
    return GREEN


def _energy_card(icon, value, label, value_style, styles):
    card = Table(
        [
            [Paragraph(icon, styles["EnergyLabel"])],
            [Paragraph(value, value_style)],
            [Paragraph(label, styles["EnergyLabel"])],
        ],
        colWidths=[1.95 * inch],
    )
    card.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
                ("BOX", (0, 0), (-1, -1), 1, SOLAR_YELLOW),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("ROUNDEDCORNERS", [8, 8, 8, 8]),
            ]
        )
    )
    return card


def _recommendation_card(number, text, styles):
    content = Table(
        [[Paragraph(str(number), styles["RecNumber"]), Paragraph(text, styles["RecBody"])]],
        colWidths=[0.35 * inch, 5.9 * inch],
    )
    content.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    box = Table([[content]], colWidths=[6.5 * inch])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
                ("BOX", (0, 0), (0, 0), 4, SOLAR_YELLOW),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("RIGHTPADDING", (0, 0), (-1, -1), 14),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    return box


def generate_farm_report(ctx, metrics, forecast_rows, recommendations, report_date, report_time):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=48,
        leftMargin=48,
        topMargin=36,
        bottomMargin=48,
    )
    styles = _build_styles()
    story = []
    shield_label = ctx["shield"] if ctx["shield"] != "READY" else "STANDBY"

    # Page 1 — Cover
    story.append(Spacer(1, 1.85 * inch))
    story.append(Paragraph("Farm Intelligence Report", styles["CoverReportTitle"]))
    info_box = Table(
        [
            ["Location", ctx["city_name"]],
            ["Date", report_date],
            ["Time", report_time],
        ],
        colWidths=[1.2 * inch, 4.5 * inch],
    )
    info_box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), DARK_BG),
                ("TEXTCOLOR", (0, 0), (0, -1), WHITE),
                ("TEXTCOLOR", (1, 0), (1, -1), TEXT_DARK),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("BOX", (0, 0), (-1, -1), 1.5, SOLAR_YELLOW),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#333333")),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    story.append(info_box)
    story.append(Spacer(1, 2.4 * inch))
    story.append(
        Paragraph("Powered by Edge AI | Generated by Solar OS v1.0", styles["CoverFooter"])
    )
    story.append(PageBreak())

    # Page 2 — Current Status
    story.append(_section_header("Current Status", styles))
    grid = Table(
        [
            [
                _metric_card("TEMP", f"{ctx['temp']} C", "Temperature", BLUE, styles),
                _metric_card("WIND", f"{ctx['wind']} km/h", "Wind Speed", PURPLE, styles),
            ],
            [
                _metric_card("SOLAR", f"{ctx['solar_output']} W/m2", "Solar Output", SOLAR_YELLOW, styles),
                _metric_card("RAIN", f"{ctx['rain']} mm", "Precipitation", TEAL, styles),
            ],
        ],
        colWidths=[3.05 * inch, 3.05 * inch],
        hAlign="CENTER",
    )
    grid.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(grid)
    story.append(Spacer(1, 0.25 * inch))

    badge_row = Table(
        [
            [
                Paragraph("<b>Shield Status</b>", styles["HighlightBox"]),
                Paragraph("<b>Threat Level</b>", styles["HighlightBox"]),
            ],
            [
                _status_badge(shield_label, _shield_badge(ctx["shield"]), styles),
                _status_badge(ctx["threat_level"], _threat_badge_color(ctx["threat_level"]), styles),
            ],
        ],
        colWidths=[3.05 * inch, 3.05 * inch],
    )
    badge_row.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("BOTTOMPADDING", (0, 0), (-1, 0), 6)]))
    story.append(badge_row)
    story.append(Spacer(1, 0.2 * inch))

    decision_box = Table(
        [
            [Paragraph(f"<b>Energy Mode:</b> {ctx['mode'].title()}", styles["HighlightBox"])],
            [Paragraph(f"<b>AI Decision:</b> {ctx['status']} — {ctx['action']}", styles["HighlightBox"])],
        ],
        colWidths=[6.2 * inch],
    )
    decision_box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF8E7")),
                ("BOX", (0, 0), (-1, -1), 1.5, SOLAR_YELLOW),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("ROUNDEDCORNERS", [6, 6, 6, 6]),
            ]
        )
    )
    story.append(decision_box)
    story.append(PageBreak())

    # Page 3 — Energy Analysis
    story.append(_section_header("Energy Analysis", styles))
    energy_row1 = Table(
        [
            [
                _energy_card("Daily", f"{metrics['daily_energy_kwh']} kWh", "Daily Energy", styles["EnergyValueYellow"], styles),
                _energy_card("Annual", f"{metrics['annual_energy_kwh']:,.0f} kWh", "Annual Energy", styles["EnergyValueYellow"], styles),
                _energy_card("H2", f"{metrics['h2_kg']} kg", "H2 Generated Today", styles["EnergyValueYellow"], styles),
            ]
        ],
        colWidths=[2.05 * inch, 2.05 * inch, 2.05 * inch],
    )
    energy_row1.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    energy_row2 = Table(
        [
            [
                _energy_card("Savings", f"Rs. {metrics['annual_savings_inr']:,.0f}", "Annual Savings", styles["EnergyValueGreen"], styles),
                _energy_card("CO2", f"{metrics['co2_saved_kg']:,.0f} kg/yr", "CO2 Saved", styles["EnergyValueGreen"], styles),
                _energy_card("Diesel", f"{metrics['diesel_displaced_litres']:,.0f} L/yr", "Diesel Displaced", styles["EnergyValueGreen"], styles),
            ]
        ],
        colWidths=[2.05 * inch, 2.05 * inch, 2.05 * inch],
    )
    energy_row2.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    story.append(energy_row1)
    story.append(Spacer(1, 0.15 * inch))
    story.append(energy_row2)
    story.append(Spacer(1, 0.2 * inch))
    story.append(
        Paragraph(
            f"<b>Farm Size:</b> {metrics['farm_size']} kW  |  "
            f"<b>Electricity Rate:</b> Rs. {metrics['electricity_rate']}/kWh",
            styles["HighlightBox"],
        )
    )
    story.append(PageBreak())

    # Page 4 — 7-Day Forecast
    story.append(_section_header("7-Day Forecast Summary", styles))
    forecast_table_data = [["Date", "Est Output", "Rain (mm)", "AI Plan", "Status"]]
    row_styles = []
    for row in forecast_rows:
        forecast_table_data.append(
            [row["Date"], str(row["Est Output"]), str(row["Rain"]), row["AI Plan"], row["Status"]]
        )
        row_styles.append(row.get("row_type", "neutral"))

    forecast_table = Table(
        forecast_table_data,
        colWidths=[1.1 * inch, 0.95 * inch, 0.75 * inch, 1.55 * inch, 1.15 * inch],
    )
    table_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), SOLAR_YELLOW),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    for i, row_type in enumerate(row_styles, start=1):
        if row_type == "rain":
            table_cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT_RED))
        elif row_type == "good":
            table_cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GREEN))
        elif i % 2 == 0:
            table_cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GREY))
    forecast_table.setStyle(TableStyle(table_cmds))
    story.append(forecast_table)
    story.append(PageBreak())

    # Page 5 — Recommendations
    story.append(_section_header("AI Recommendations", styles))
    for i, rec in enumerate(recommendations, 1):
        story.append(_recommendation_card(i, rec, styles))
        story.append(Spacer(1, 0.12 * inch))

    doc.build(story, onFirstPage=_draw_cover_header)
    buffer.seek(0)
    return buffer.getvalue()
