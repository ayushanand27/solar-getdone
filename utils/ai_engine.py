from utils.weather import radiation_index


def ai_decision(wcode, wind, rain, radiation, sim_event, hours=None):
    hr = radiation_index(radiation, hours)
    dust_factor = 0.75 if sim_event == "dust" else 1.0
    solar_output = round(radiation[hr] * 0.22 * dust_factor, 1)

    if wcode >= 95:
        return (
            "🛡️ SHIELD CLOSED",
            "Thunderstorm detected — panels protected",
            "protection",
            solar_output,
            "CLOSED",
            "Thunderstorm detected",
            "CRITICAL",
        )
    if wcode >= 61 or rain > 0.5:
        return (
            "🛡️ SHIELD CLOSED",
            "Heavy rain — panels protected",
            "protection",
            solar_output,
            "CLOSED",
            "Heavy rainfall detected",
            "HIGH",
        )
    if wind > 60:
        return (
            "🛡️ SHIELD CLOSED",
            "Extreme wind — panels protected",
            "protection",
            solar_output,
            "CLOSED",
            "Extreme wind speed",
            "HIGH",
        )
    if sim_event == "bird":
        return (
            "🛡️ SHIELD PARTIAL",
            "Bird activity — deterrent active, partial shield",
            "monitor",
            solar_output,
            "READY",
            "Bird swarm detected by camera",
            "MEDIUM",
        )
    if sim_event == "dust":
        return (
            "⚠️ DUST ALERT",
            "Dust storm — auto-clean sequence triggered (25% efficiency loss)",
            "monitor",
            solar_output,
            "READY",
            "Dust levels critical",
            "MEDIUM",
        )
    if wind > 40:
        return (
            "⚠️ MONITORING",
            "High wind — monitoring closely",
            "monitor",
            solar_output,
            "READY",
            "Wind speed elevated — shield on standby",
            "MEDIUM",
        )
    if solar_output > 150:
        return (
            "⚡ FULL CONVERSION",
            "Peak sunlight — maximum energy harvesting",
            "harvest",
            solar_output,
            "OPEN",
            "Clear sky — full exposure",
            "LOW",
        )
    if solar_output > 50:
        return (
            "🔋 STORING + H₂",
            "Moderate sunlight — storing battery + making hydrogen",
            "store",
            solar_output,
            "OPEN",
            "Normal conditions",
            "LOW",
        )
    return (
        "🌙 DISTRIBUTING",
        "Low/no sunlight — distributing stored energy",
        "distribute",
        solar_output,
        "OPEN",
        "No threat detected",
        "LOW",
    )


def detect_anomaly(radiation_history: list) -> dict:
    if len(radiation_history) < 2:
        return {"anomaly": False}

    current = radiation_history[-1]
    previous = radiation_history[-2]

    if previous == 0:
        return {"anomaly": False}

    drop_pct = ((previous - current) / previous) * 100

    if drop_pct > 30:
        return {
            "anomaly": True,
            "type": "sudden_drop",
            "drop_pct": round(drop_pct, 1),
            "message": f"Solar output dropped {round(drop_pct, 1)}% in 1 hour — possible cloud cover, dust, or panel damage",
        }
    return {"anomaly": False}
