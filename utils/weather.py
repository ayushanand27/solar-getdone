import requests
import streamlit as st


@st.cache_data(ttl=300)
def get_coordinates(city):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    r = requests.get(url)
    data = r.json()
    if "results" in data and len(data["results"]) > 0:
        result = data["results"][0]
        return result["latitude"], result["longitude"], result["name"]
    return 26.9124, 75.7873, "Jaipur"


@st.cache_data(ttl=300)
def get_weather(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,weathercode,windspeed_10m,precipitation"
        f"&hourly=shortwave_radiation"
        f"&forecast_days=1"
    )
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if "current" not in data:
            raise ValueError("No current data")
        return data
    except Exception:
        return {
            "current": {
                "temperature_2m": 30,
                "weathercode": 0,
                "windspeed_10m": 10,
                "precipitation": 0,
            },
            "hourly": {
                "shortwave_radiation": [
                    0, 0, 0, 0, 0, 10, 50, 120, 180, 200, 195, 185, 160, 120, 80, 40, 10, 0, 0, 0, 0, 0, 0, 0
                ],
                "time": [f"2026-06-05T{h:02d}:00" for h in range(24)],
            },
        }


@st.cache_data(ttl=3600)
def get_7day(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&daily=weathercode,shortwave_radiation_sum,precipitation_sum,windspeed_10m_max"
        f"&forecast_days=7&timezone=auto"
    )
    try:
        r = requests.get(url, timeout=10)
        return r.json()
    except Exception:
        return {
            "daily": {
                "weathercode": [0] * 7,
                "shortwave_radiation_sum": [5000] * 7,
                "precipitation_sum": [0] * 7,
                "windspeed_10m_max": [15] * 7,
                "time": [f"2026-06-0{i + 3}" for i in range(7)],
            }
        }
