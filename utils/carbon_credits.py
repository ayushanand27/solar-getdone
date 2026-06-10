from datetime import datetime
from io import BytesIO

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

INDIA_CREDIT_PRICE_INR = 1500
VCM_CREDIT_PRICE_USD = 7
FOSSIL_COST_PER_KWH_INR = 7

GREEN = colors.HexColor("#00C896")
DARK = colors.HexColor("#0D1117")
GREY = colors.HexColor("#8B949E")


def derive_daily_hours(ctx):
    radiation = ctx.get("radiation", [])
    if radiation:
        hours = sum(1 for r in radiation if r * 0.22 > 50)
        return max(3.5, min(8.5, hours))
    return max(3.5, min(8.5, ctx.get("solar_output", 120) / 30))


def renewable_pct(ctx):
    radiation = ctx.get("radiation", [])
    if not radiation:
        return 85.0
    productive = sum(1 for r in radiation if r > 50)
    return round((productive / len(radiation)) * 100, 1)


def governance_score(session_state):
    try:
        from utils.compliance_report import calculate_score, init_compliance_state

        init_compliance_state()
        return calculate_score(session_state.get("cea_compliance", {}))
    except Exception:
        return 72


def calculate_metrics(farm_size_kw, years, emission_factor, ctx):
    daily_hours = derive_daily_hours(ctx)
    annual_energy_kwh = round(farm_size_kw * daily_hours * 365, 1)
    co2_avoided_tonnes = round(annual_energy_kwh * emission_factor / 1000, 2)
    carbon_credits = co2_avoided_tonnes
    india_revenue = round(carbon_credits * INDIA_CREDIT_PRICE_INR, 0)
    vcm_revenue = round(carbon_credits * VCM_CREDIT_PRICE_USD, 0)
    fossil_cost = round(annual_energy_kwh * FOSSIL_COST_PER_KWH_INR, 0)

    return {
        "daily_hours": daily_hours,
        "annual_energy_kwh": annual_energy_kwh,
        "co2_avoided_tonnes": co2_avoided_tonnes,
        "carbon_credits": carbon_credits,
        "india_revenue_inr": india_revenue,
        "vcm_revenue_usd": vcm_revenue,
        "fossil_cost_inr": fossil_cost,
        "years": years,
    }


def build_projection(metrics, projection_years=25):
    rows = []
    cumulative_co2 = 0.0
    cumulative_revenue_inr = 0.0
    cumulative_savings_inr = 0.0

    for year in range(1, projection_years + 1):
        degradation = 1 - (year - 1) * 0.005
        annual_co2 = metrics["co2_avoided_tonnes"] * degradation
        annual_revenue = metrics["india_revenue_inr"] * degradation
        annual_fossil = metrics["fossil_cost_inr"] * degradation
        cumulative_co2 += annual_co2
        cumulative_revenue_inr += annual_revenue
        cumulative_savings_inr += annual_fossil
        rows.append(
            {
                "Year": year,
                "Annual CO₂ Avoided (tonnes)": round(annual_co2, 2),
                "Cumulative CO₂ (tonnes)": round(cumulative_co2, 2),
                "Cumulative Credit Revenue (₹)": round(cumulative_revenue_inr, 0),
                "Cumulative Fossil Savings (₹)": round(cumulative_savings_inr, 0),
            }
        )
    return pd.DataFrame(rows)


def calculate_esg(metrics, ctx, governance):
    renewable = renewable_pct(ctx)
    env_score = min(
        100,
        round(
            40
            + min(40, metrics["co2_avoided_tonnes"] / 50 * 40)
            + renewable * 0.2
        ),
    )

    households = max(50, int(metrics["annual_energy_kwh"] / 1200))
    jobs = max(2, int(metrics["annual_energy_kwh"] / 500000) + 3)
    social_score = min(100, round(55 + min(25, households / 200) + min(20, jobs * 3)))

    esg_overall = round((env_score + social_score + governance) / 3)

    return {
        "environment": env_score,
        "social": social_score,
        "governance": governance,
        "overall": esg_overall,
        "grade": (
            "🟢 Leader" if esg_overall >= 80 else "🟡 Progressing" if esg_overall >= 60 else "🔴 Developing"
        ),
        "households": households,
        "jobs": jobs,
        "renewable_pct": renewable,
    }


def build_comparison_table(farm_size_kw, metrics):
    annual_mwh = metrics["annual_energy_kwh"] / 1000
    coal_co2 = round(annual_mwh * 950, 1)
    gas_co2 = round(annual_mwh * 450, 1)
    grid_co2 = round(annual_mwh * 710, 1)

    return pd.DataFrame(
        [
            {
                "Source": "☀️ Solar OS Farm",
                "Capacity (kW)": farm_size_kw,
                "CO₂/year (tonnes)": 0,
                "Water/year (ML)": round(annual_mwh * 0.02, 2),
                "Energy Cost/year (₹)": round(metrics["annual_energy_kwh"] * 2.5, 0),
                "Carbon Credits/year": metrics["carbon_credits"],
            },
            {
                "Source": "🪨 Coal Plant",
                "Capacity (kW)": farm_size_kw,
                "CO₂/year (tonnes)": coal_co2,
                "Water/year (ML)": round(annual_mwh * 2.5, 2),
                "Energy Cost/year (₹)": round(metrics["annual_energy_kwh"] * 6.5, 0),
                "Carbon Credits/year": 0,
            },
            {
                "Source": "🔥 Gas Plant",
                "Capacity (kW)": farm_size_kw,
                "CO₂/year (tonnes)": gas_co2,
                "Water/year (ML)": round(annual_mwh * 0.8, 2),
                "Energy Cost/year (₹)": round(metrics["annual_energy_kwh"] * 5.2, 0),
                "Carbon Credits/year": 0,
            },
            {
                "Source": "⚡ Grid Only (no solar)",
                "Capacity (kW)": farm_size_kw,
                "CO₂/year (tonnes)": grid_co2,
                "Water/year (ML)": round(annual_mwh * 0.3, 2),
                "Energy Cost/year (₹)": metrics["fossil_cost_inr"],
                "Carbon Credits/year": 0,
            },
        ]
    )


def generate_esg_pdf(farm_name, metrics, esg, projection_df, comparison_df, report_date):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], alignment=TA_CENTER, textColor=DARK, fontSize=20)
    sub_style = ParagraphStyle("Sub", parent=styles["Normal"], alignment=TA_CENTER, textColor=GREY, fontSize=11)
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14)

    story = [
        Paragraph("ESG &amp; Carbon Credit Report", title_style),
        Spacer(1, 0.15 * inch),
        Paragraph(f"Farm: <b>{farm_name}</b>", sub_style),
        Paragraph(f"Date: {report_date}", sub_style),
        Paragraph("India Carbon Credit Market 2026", sub_style),
        Spacer(1, 0.3 * inch),
        Paragraph("<b>Carbon Metrics</b>", body),
        Spacer(1, 0.1 * inch),
        Paragraph(
            f"Annual Energy: {metrics['annual_energy_kwh']:,.0f} kWh<br/>"
            f"Annual CO₂ Avoided: {metrics['co2_avoided_tonnes']:,.2f} tonnes<br/>"
            f"Carbon Credits Generated: {metrics['carbon_credits']:,.2f} credits<br/>"
            f"India CCTS Revenue: ₹{metrics['india_revenue_inr']:,.0f}/year<br/>"
            f"International VCM Revenue: ${metrics['vcm_revenue_usd']:,.0f}/year",
            body,
        ),
        Spacer(1, 0.25 * inch),
        Paragraph("<b>25-Year Projection Summary</b>", body),
        Spacer(1, 0.1 * inch),
    ]

    final_row = projection_df.iloc[-1]
    story.append(
        Paragraph(
            f"Cumulative CO₂ avoided: {final_row['Cumulative CO₂ (tonnes)']:,.1f} tonnes<br/>"
            f"Cumulative credit revenue: ₹{final_row['Cumulative Credit Revenue (₹)']:,.0f}<br/>"
            f"Cumulative fossil savings: ₹{final_row['Cumulative Fossil Savings (₹)']:,.0f}",
            body,
        )
    )
    story.append(Spacer(1, 0.25 * inch))
    story.append(Paragraph("<b>ESG Scores</b>", body))
    story.append(Spacer(1, 0.1 * inch))
    story.append(
        Paragraph(
            f"Environment: {esg['environment']}/100 · "
            f"Social: {esg['social']}/100 · "
            f"Governance: {esg['governance']}/100<br/>"
            f"Overall ESG: {esg['overall']}/100 — {esg['grade']}",
            body,
        )
    )
    story.append(Spacer(1, 0.25 * inch))
    story.append(Paragraph("<b>Source Comparison</b>", body))
    story.append(Spacer(1, 0.1 * inch))

    comp_rows = [["Source", "CO₂/year (t)", "Water/year (ML)", "Cost/year (₹)", "Credits"]]
    for _, row in comparison_df.iterrows():
        comp_rows.append(
            [
                row["Source"],
                str(row["CO₂/year (tonnes)"]),
                str(row["Water/year (ML)"]),
                str(row["Energy Cost/year (₹)"]),
                str(row["Carbon Credits/year"]),
            ]
        )
    table = Table(comp_rows, colWidths=[1.6 * inch, 0.9 * inch, 1.0 * inch, 1.1 * inch, 0.8 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph("<i>Generated by Solar OS — Carbon Credits &amp; ESG Module</i>", sub_style))

    doc.build(story)
    return buffer.getvalue()
