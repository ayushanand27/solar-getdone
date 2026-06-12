from datetime import datetime, timedelta

import pandas as pd

from utils.pdf_text import clean_pdf_text


def _clamp(score):
    return max(0, min(100, round(score)))


def dry_streak_days(ctx):
    streak = 0
    daily = ctx.get("forecast", {}).get("daily", {})
    precip = daily.get("precipitation_sum", [])
    if precip:
        for p in precip:
            if p < 0.5:
                streak += 1
            else:
                break
        return streak
    return 7 if ctx.get("rain", 0) < 0.5 else 0


def storm_exposure_count(ctx):
    daily = ctx.get("forecast", {}).get("daily", {})
    codes = daily.get("weathercode", [])
    return sum(1 for c in codes if c >= 95)


def radiation_fluctuation(ctx):
    radiation = ctx.get("radiation", [])
    if len(radiation) < 2:
        return 0
    outputs = [r * 0.22 for r in radiation]
    mean = sum(outputs) / len(outputs)
    if mean == 0:
        return 0
    variance = sum((o - mean) ** 2 for o in outputs) / len(outputs)
    return (variance ** 0.5) / mean * 100


def panel_health_score(ctx):
    score = 100
    dry_days = dry_streak_days(ctx)
    if dry_days >= 7:
        score -= min(35, (dry_days - 6) * 8)
    elif dry_days >= 4:
        score -= 15

    if ctx.get("temp", 0) > 40:
        score -= 25
    elif ctx.get("temp", 0) > 35:
        score -= 12

    if ctx.get("wind", 0) > 50:
        score -= 20
    elif ctx.get("wind", 0) > 40:
        score -= 10

    if ctx.get("sim_event") == "dust":
        score -= 20

    return _clamp(score)


def inverter_health_score(ctx):
    score = 100
    operating_hours = sum(1 for r in ctx.get("radiation", []) if r > 100)
    if operating_hours > 10:
        score -= min(18, (operating_hours - 8) * 2)

    if ctx.get("temp", 0) > 38:
        score -= 20
    elif ctx.get("temp", 0) > 33:
        score -= 8

    fluctuation = radiation_fluctuation(ctx)
    if fluctuation > 40:
        score -= 22
    elif fluctuation > 25:
        score -= 12

    return _clamp(score)


def battery_health_score(ctx):
    battery_level = min(100, int(ctx.get("solar_output", 0) / 2))
    score = 100

    if battery_level < 20:
        score -= 35
    elif battery_level < 40:
        score -= 18
    elif battery_level < 60:
        score -= 8

    h2_kg = round(sum(r * 0.22 * 0.7 for r in ctx.get("radiation", []) if r > 100) / 1000, 2)
    cycles_est = int(h2_kg * 40)
    if cycles_est > 85:
        score -= 15
    elif cycles_est > 70:
        score -= 8

    if ctx.get("temp", 0) > 40:
        score -= 18
    elif ctx.get("temp", 0) > 35:
        score -= 8

    return _clamp(score)


def structural_health_score(ctx):
    score = 100
    storms = storm_exposure_count(ctx)
    score -= min(30, storms * 10)

    wind = ctx.get("wind", 0)
    if wind > 60:
        score -= 28
    elif wind > 50:
        score -= 18
    elif wind > 40:
        score -= 10

    if ctx.get("wcode", 0) >= 95:
        score -= 15

    return _clamp(score)


def subsystem_scores(ctx):
    return {
        "Panel Health": panel_health_score(ctx),
        "Inverter Health": inverter_health_score(ctx),
        "Battery Health": battery_health_score(ctx),
        "Structural Health": structural_health_score(ctx),
    }


def overall_health_score(scores):
    if not scores:
        return 0
    return _clamp(sum(scores.values()) / len(scores))


def urgency_label(probability, days):
    if probability >= 70 or days <= 3:
        return "🔴 High"
    if probability >= 40 or days <= 14:
        return "🟡 Medium"
    return "🟢 Low"


def build_predictions(ctx, scores):
    dry_days = dry_streak_days(ctx)
    predictions = []

    dust_prob = min(95, 40 + dry_days * 7 + (15 if ctx.get("sim_event") == "dust" else 0))
    if dust_prob >= 20:
        predictions.append(
            {
                "Component": "Panels",
                "Issue": "Dust buildup",
                "Probability": f"{dust_prob}%",
                "Recommended Action": "Clean panels",
                "Urgency": urgency_label(dust_prob, max(2, 10 - dry_days)),
                "Days Until Required": max(2, 10 - dry_days),
            }
        )

    thermal_prob = min(90, 20 + max(0, ctx.get("temp", 0) - 30) * 3)
    if scores["Inverter Health"] < 85:
        predictions.append(
            {
                "Component": "Inverter",
                "Issue": "Thermal stress",
                "Probability": f"{int(thermal_prob * 0.6 + (100 - scores['Inverter Health']) * 0.4)}%",
                "Recommended Action": "Check cooling fans and ventilation",
                "Urgency": urgency_label(thermal_prob, 14),
                "Days Until Required": 14,
            }
        )

    battery_level = min(100, int(ctx.get("solar_output", 0) / 2))
    discharge_prob = min(80, max(15, 100 - battery_level - 20))
    if battery_level < 70:
        predictions.append(
            {
                "Component": "Battery",
                "Issue": "Deep discharge risk",
                "Probability": f"{discharge_prob}%",
                "Recommended Action": "Adjust charging schedule",
                "Urgency": urgency_label(discharge_prob, 30),
                "Days Until Required": 30,
            }
        )

    wind_prob = min(75, 10 + ctx.get("wind", 0) + storm_exposure_count(ctx) * 8)
    if scores["Structural Health"] < 90:
        predictions.append(
            {
                "Component": "Structure",
                "Issue": "Wind fatigue",
                "Probability": f"{wind_prob}%",
                "Recommended Action": "Inspect panel mounts and torque bolts",
                "Urgency": urgency_label(wind_prob, 60),
                "Days Until Required": 60,
            }
        )

    if ctx.get("temp", 0) > 40 and scores["Panel Health"] < 80:
        predictions.append(
            {
                "Component": "Panels",
                "Issue": "Heat degradation",
                "Probability": f"{min(88, 50 + int(ctx['temp'] - 38) * 5)}%",
                "Recommended Action": "Increase ventilation under arrays",
                "Urgency": urgency_label(75, 5),
                "Days Until Required": 5,
            }
        )

    return sorted(predictions, key=lambda p: p["Days Until Required"])


def build_calendar(predictions):
    today = datetime.now().date()
    rows = []
    scheduled = {p["Days Until Required"]: p for p in predictions}

    for offset in range(30):
        day = today + timedelta(days=offset)
        event = scheduled.get(offset)
        if event:
            rows.append(
                {
                    "Date": day.strftime("%Y-%m-%d"),
                    "Day": day.strftime("%a"),
                    "Task": f"{event['Component']}: {event['Recommended Action']}",
                    "Priority": event["Urgency"],
                }
            )
        elif offset % 10 == 0:
            rows.append(
                {
                    "Date": day.strftime("%Y-%m-%d"),
                    "Day": day.strftime("%a"),
                    "Task": "Routine visual inspection",
                    "Priority": "🟢 Routine",
                }
            )
        else:
            rows.append(
                {
                    "Date": day.strftime("%Y-%m-%d"),
                    "Day": day.strftime("%a"),
                    "Task": "—",
                    "Priority": "🟢 Routine",
                }
            )
    return pd.DataFrame(rows)


def maintenance_costs(overall_score, farm_size_kw=500):
    reactive = round(farm_size_kw * 420 * (1 + (100 - overall_score) / 100))
    predictive = round(reactive * 0.62)
    savings = reactive - predictive
    return reactive, predictive, savings
