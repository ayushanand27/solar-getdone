def calculate_health_score(solar_output, threat_level, battery, h2_level, shield, wind, rain, wcode):
    score = 100

    if threat_level == "CRITICAL":
        score -= 40
    elif threat_level == "HIGH":
        score -= 25
    elif threat_level == "MEDIUM":
        score -= 10

    if wcode >= 95:
        score -= 20
    elif wcode >= 61:
        score -= 10
    if wind > 60:
        score -= 15
    elif wind > 40:
        score -= 5

    if shield == "CLOSED":
        score -= 10
    elif shield == "READY":
        score -= 5

    if solar_output > 150:
        score += 5
    elif solar_output < 20:
        score -= 10

    if 30 < battery < 80:
        score += 5

    score = max(0, min(100, score))

    if score >= 80:
        grade = "🟢 Excellent"
    elif score >= 60:
        grade = "🟡 Good"
    elif score >= 40:
        grade = "🟠 Fair"
    else:
        grade = "🔴 Critical"

    return score, grade
