"""Solar OS integration health check — run: python scripts/health_check.py"""
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"
results = []


def safe(text):
    return str(text).encode("ascii", errors="replace").decode("ascii")


def record(name, status, detail=""):
    results.append((name, status, detail))
    icon = {"PASS": "+", "FAIL": "X", "WARN": "!"}.get(status, "?")
    line = f"[{icon}] {safe(name)}: {status}"
    if detail:
        line += f" -- {safe(detail)}"
    print(line)


def load_secrets():
    secrets_path = ROOT / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        return {}
    with open(secrets_path, "rb") as f:
        return tomllib.load(f)


def test_imports():
    modules = [
        "app",
        "utils.weather",
        "utils.ai_engine",
        "utils.health_score",
        "utils.cv_module",
        "utils.mqtt_client",
        "utils.mobile_alerts",
        "utils.app_state",
        "utils.mqtt_sim",
        "utils.email_alerts",
        "utils.pdf_report",
    ]
    for mod in modules:
        try:
            __import__(mod)
            record(f"import {mod}", PASS)
        except Exception as e:
            record(f"import {mod}", FAIL, str(e))


def test_weather_api():
    from utils.weather import get_coordinates, get_weather

    try:
        lat, lon, city = get_coordinates("Jaipur")
        assert isinstance(lat, float) and isinstance(lon, float)
        record("Open-Meteo Geocoding", PASS, f"{city} ({lat:.2f}, {lon:.2f})")
    except Exception as e:
        record("Open-Meteo Geocoding", FAIL, str(e))
        return

    try:
        get_coordinates.clear()
        data = get_weather(lat, lon)
        assert "current" in data and "hourly" in data
        temp = data["current"]["temperature_2m"]
        record("Open-Meteo Weather", PASS, f"temp={temp}°C, hours={len(data['hourly']['shortwave_radiation'])}")
    except Exception as e:
        record("Open-Meteo Weather", FAIL, str(e))


def test_ai_engine():
    from utils.ai_engine import ai_decision, detect_anomaly

    try:
        radiation = [0] * 12 + [200] * 12
        result = ai_decision(0, 10, 0, radiation, None)
        assert len(result) == 7
        record("AI Decision Engine", PASS, f"mode={result[2]}, output={result[3]} W/m²")
    except Exception as e:
        record("AI Decision Engine", FAIL, str(e))

    try:
        anomaly = detect_anomaly([200, 100])
        assert anomaly["anomaly"] is True
        record("Anomaly Detection", PASS, f"drop={anomaly['drop_pct']}%")
    except Exception as e:
        record("Anomaly Detection", FAIL, str(e))


def test_health_score():
    from utils.health_score import calculate_health_score

    try:
        score, grade = calculate_health_score(150, "LOW", 80, 60, "OPEN", 10, 0, 0)
        assert 0 <= score <= 100
        record("Health Score", PASS, f"{score}/100 {grade}")
    except Exception as e:
        record("Health Score", FAIL, str(e))


def test_cv_module():
    from utils.cv_module import filename_threat_override, get_cv_verdict

    try:
        threat, conf = filename_threat_override("bs1.png")
        assert threat == "bird"
        verdict, _ = get_cv_verdict(threat)
        record("CV Module (sample logic)", PASS, f"bs1→{threat} ({conf}), verdict={verdict}")
    except Exception as e:
        record("CV Module (sample logic)", FAIL, str(e))


def test_mqtt(secrets):
    mqtt = secrets.get("mqtt", {})
    if not mqtt.get("host"):
        record("HiveMQ MQTT", WARN, "No mqtt secrets configured")
        return

    try:
        from utils.mqtt_client import publish_to_hivemq

        ok, msg = publish_to_hivemq(120.0, 32.0, 15.0, "OPEN", "harvest", "LOW")
        record("HiveMQ MQTT", PASS if ok else FAIL, msg)
    except Exception as e:
        record("HiveMQ MQTT", FAIL, str(e))


def test_groq(secrets):
    groq_cfg = secrets.get("groq", {})
    api_key = groq_cfg.get("api_key", "")
    if not api_key or api_key == "YOUR_GROQ_API_KEY":
        record("Groq AI Assistant", WARN, "No API key configured")
        return

    try:
        from groq import Groq

        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Reply with exactly: Solar OS OK"}],
            max_tokens=20,
        )
        reply = response.choices[0].message.content.strip()
        record("Groq AI Assistant", PASS, f"reply={reply[:60]}")
    except Exception as e:
        err = str(e)
        if "decommissioned" in err.lower() or "model" in err.lower():
            record("Groq AI Assistant", WARN, f"Model issue: {err[:120]}")
        else:
            record("Groq AI Assistant", FAIL, err[:120])


def test_mobile_alerts():
    try:
        from utils.mobile_alerts import battery_level, h2_tank_level, process_auto_alerts

        assert battery_level(200) == 100
        ctx = {
            "city_name": "Jaipur",
            "sim_event": None,
            "wcode": 0,
            "solar_output": 100,
            "radiation": [150] * 24,
        }
        config = {"storm": True, "bird_dust": True, "battery": True, "h2_full": True, "peak": True}
        process_auto_alerts(ctx, config)
        record("Mobile Alerts", PASS, "process_auto_alerts ran without error")
    except Exception as e:
        record("Mobile Alerts", FAIL, str(e))


def test_pdf_report():
    try:
        from datetime import datetime

        from utils.pdf_report import (
            build_forecast_rows,
            build_recommendations,
            compute_analytics_metrics,
            generate_farm_report,
        )

        ctx = {
            "city_name": "Jaipur",
            "temp": 30,
            "wind": 10,
            "rain": 0,
            "solar_output": 150,
            "shield": "OPEN",
            "threat_level": "LOW",
            "mode": "harvest",
            "status": "FULL CONVERSION",
            "action": "Peak sunlight harvesting",
            "rain": 0,
            "radiation": [150] * 24,
            "hours": [f"2026-06-05T{h:02d}:00" for h in range(24)],
            "sim_event": None,
            "wcode": 0,
            "forecast": {
                "daily": {
                    "time": [f"2026-06-0{i + 3}" for i in range(7)],
                    "weathercode": [0, 61, 0, 0, 95, 0, 0],
                    "shortwave_radiation_sum": [5000, 2000, 6000, 5500, 1000, 7000, 6500],
                    "precipitation_sum": [0, 3, 0, 0, 5, 0, 0],
                }
            },
        }
        metrics = compute_analytics_metrics(ctx, 100, 7, 90)
        forecast_rows = build_forecast_rows(ctx)
        recommendations = build_recommendations(ctx, metrics)
        now = datetime.now()
        pdf_bytes = generate_farm_report(
            ctx, metrics, forecast_rows, recommendations, now.strftime("%Y-%m-%d"), now.strftime("%H:%M")
        )
        assert pdf_bytes and len(pdf_bytes) > 1000
        record("PDF Report", PASS, f"{len(pdf_bytes):,} bytes")
    except Exception as e:
        record("PDF Report", FAIL, str(e))


def test_page_syntax():
    pages = sorted((ROOT / "pages").glob("*.py"))
    import py_compile

    for page in pages:
        try:
            py_compile.compile(str(page), doraise=True)
            record(f"syntax {page.name}", PASS)
        except Exception as e:
            record(f"syntax {page.name}", FAIL, str(e))


def main():
    print("=" * 60)
    print("Solar OS Health Check")
    print("=" * 60)

    secrets = load_secrets()
    test_imports()
    test_page_syntax()
    test_weather_api()
    test_ai_engine()
    test_health_score()
    test_cv_module()
    test_mqtt(secrets)
    test_groq(secrets)
    test_mobile_alerts()
    test_pdf_report()

    passed = sum(1 for _, s, _ in results if s == PASS)
    failed = sum(1 for _, s, _ in results if s == FAIL)
    warned = sum(1 for _, s, _ in results if s == WARN)

    print("=" * 60)
    print(f"Summary: {passed} passed, {failed} failed, {warned} warnings")
    print("=" * 60)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
