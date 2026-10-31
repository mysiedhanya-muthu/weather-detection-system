"""
Weather service module for AI Weather Disaster Early Warning System.
Fetches real-time, hourly, and 7-day meteorological forecast data from Open-Meteo
with fallback handling and WMO code interpretation.
"""

import requests
import math
from typing import Dict, Any, List, Optional

WMO_WEATHER_CODES = {
    0: {"desc": "Clear sky", "category": "clear", "icon": "☀️"},
    1: {"desc": "Mainly clear", "category": "clear", "icon": "🌤️"},
    2: {"desc": "Partly cloudy", "category": "cloudy", "icon": "⛅"},
    3: {"desc": "Overcast", "category": "cloudy", "icon": "☁️"},
    45: {"desc": "Fog", "category": "fog", "icon": "🌫️"},
    48: {"desc": "Depositing rime fog", "category": "fog", "icon": "🌫️"},
    51: {"desc": "Light drizzle", "category": "rain", "icon": "🌦️"},
    53: {"desc": "Moderate drizzle", "category": "rain", "icon": "🌧️"},
    55: {"desc": "Dense drizzle", "category": "rain", "icon": "🌧️"},
    61: {"desc": "Slight rain", "category": "rain", "icon": "🌧️"},
    63: {"desc": "Moderate rain", "category": "rain", "icon": "🌧️"},
    65: {"desc": "Heavy rain downpour", "category": "heavy_rain", "icon": "⛈️"},
    71: {"desc": "Slight snow fall", "category": "snow", "icon": "🌨️"},
    73: {"desc": "Moderate snow fall", "category": "snow", "icon": "❄️"},
    75: {"desc": "Heavy snow blizzard", "category": "snow", "icon": "❄️"},
    80: {"desc": "Slight rain showers", "category": "rain", "icon": "🌦️"},
    81: {"desc": "Moderate rain showers", "category": "rain", "icon": "🌧️"},
    82: {"desc": "Violent rain torrential downpour", "category": "heavy_rain", "icon": "⛈️"},
    85: {"desc": "Slight snow showers", "category": "snow", "icon": "🌨️"},
    86: {"desc": "Heavy snow showers", "category": "snow", "icon": "❄️"},
    95: {"desc": "Thunderstorm", "category": "thunderstorm", "icon": "⚡"},
    96: {"desc": "Thunderstorm with slight hail", "category": "thunderstorm", "icon": "⛈️"},
    99: {"desc": "Severe thunderstorm with heavy hail", "category": "thunderstorm", "icon": "🌩️"}
}

def get_climate_image(category: str, temp_c: float, precip_24h: float) -> str:
    """
    Select appropriate high-impact climate picture based on current meteorological
    context and hazard indicators.
    """
    if precip_24h > 65:
        return "/static/images/weather_flood.jpg"
    elif category == "thunderstorm":
        return "/static/images/weather_thunderstorm.jpg"
    elif category == "heavy_rain" or precip_24h > 35:
        return "/static/images/weather_rain.jpg"
    elif temp_c >= 37.0:
        return "/static/images/weather_heatwave.jpg"
    elif category == "snow" or temp_c < -2:
        return "/static/images/weather_snow.jpg"
    elif category == "fog":
        return "/static/images/weather_fog.jpg"
    elif category == "rain":
        return "/static/images/weather_rain.jpg"
    else:
        return "/static/images/weather_clear.jpg"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ClimaShieldAI/1.0 (Disaster-Early-Warning-System)",
    "Accept": "application/json"
}

def search_locations(query: str) -> List[Dict[str, Any]]:
    """Search global locations via Open-Meteo Geocoding API with fallback."""
    if not query or len(query.strip()) < 2:
        return []
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={requests.utils.quote(query)}&count=6&language=en&format=json"
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=7)
        if resp.status_code == 200:
            data = resp.json()
            results = []
            for item in data.get("results", []):
                results.append({
                    "name": item.get("name"),
                    "country": item.get("country", ""),
                    "admin1": item.get("admin1", ""),
                    "latitude": item.get("latitude"),
                    "longitude": item.get("longitude"),
                    "timezone": item.get("timezone", "UTC")
                })
            return results
    except Exception as e:
        print(f"Geocoding error: {e}")
    return []

def generate_fallback_weather(latitude: float, longitude: float, city_name: str, country_name: str) -> Dict[str, Any]:
    """Generate realistic meteorological telemetry if external API is unreachable or rate-limited."""
    abs_lat = abs(latitude)
    if abs_lat < 23.5:
        base_temp = 29.0
        precip = 18.0
        cat = "rain"
        wmo = 61
    elif abs_lat < 55.0:
        base_temp = 19.5
        precip = 6.0
        cat = "clear"
        wmo = 1
    else:
        base_temp = 4.0
        precip = 2.0
        cat = "snow" if base_temp < 2 else "cloudy"
        wmo = 71 if base_temp < 2 else 3

    wmo_meta = WMO_WEATHER_CODES.get(wmo, {"desc": "Partly cloudy", "category": cat, "icon": "🌤️"})
    climate_img = get_climate_image(cat, base_temp, precip)

    hourly = []
    for h in range(24):
        hourly.append({
            "time": f"{h:02d}:00",
            "temp": round(base_temp + (2.5 if 10 <= h <= 16 else -2.0), 1),
            "precip": round(max(0.0, (precip / 8.0) if 13 <= h <= 17 else 0.2), 1),
            "wind": 14.0,
            "humidity": 65.0
        })

    daily = []
    import datetime
    today = datetime.date.today()
    for d in range(7):
        cur_date = today + datetime.timedelta(days=d)
        daily.append({
            "date": cur_date.isoformat(),
            "temp_max": round(base_temp + 3.0, 1),
            "temp_min": round(base_temp - 4.0, 1),
            "precip_sum": round(precip, 1),
            "precip_prob": 40,
            "wind_max": 22.0,
            "weather_desc": wmo_meta["desc"],
            "icon": wmo_meta["icon"]
        })

    return {
        "city": city_name or "Selected Location",
        "country": country_name or "",
        "latitude": latitude,
        "longitude": longitude,
        "temperature": round(base_temp, 1),
        "feels_like": round(base_temp + 1.2, 1),
        "humidity": 65.0,
        "precipitation": round(precip, 1),
        "wind_speed": 14.5,
        "wind_gusts": 22.0,
        "pressure": 1012.8,
        "pressure_drop_3h": 0.5,
        "weather_code": wmo,
        "weather_desc": wmo_meta["desc"],
        "weather_category": cat,
        "icon": wmo_meta["icon"],
        "climate_image": climate_img,
        "hourly": hourly,
        "daily": daily
    }

def fetch_weather_data(latitude: float, longitude: float, city_name: str = "", country_name: str = "") -> Dict[str, Any]:
    """Fetch current observations, hourly forecasts, and 7-day outlook from Open-Meteo with resilient fallback."""
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}&longitude={longitude}&"
        f"current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,"
        f"weather_code,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m&"
        f"hourly=temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,"
        f"surface_pressure,wind_speed_10m,wind_gusts_10m,uv_index&"
        f"daily=weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,"
        f"precipitation_sum,precipitation_hours,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max&"
        f"timezone=auto"
    )
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=7)
        if resp.status_code == 200:
            data = resp.json()
            current = data.get("current", {})
            hourly = data.get("hourly", {})
            daily = data.get("daily", {})

            wmo_code = current.get("weather_code", 0)
            wmo_meta = WMO_WEATHER_CODES.get(wmo_code, {"desc": "Clear", "category": "clear", "icon": "☀️"})

            precip_24h = daily.get("precipitation_sum", [0])[0] if daily.get("precipitation_sum") else current.get("precipitation", 0)
            temp_c = current.get("temperature_2m", 20.0)
            humidity = current.get("relative_humidity_2m", 50.0)
            wind_speed = current.get("wind_speed_10m", 10.0)
            wind_gusts = current.get("wind_gusts_10m", wind_speed * 1.3)
            pressure = current.get("surface_pressure", 1013.25)
            feels_like = current.get("apparent_temperature", temp_c)

            hourly_pressure = hourly.get("surface_pressure", [])
            pressure_drop_3h = 0.0
            if len(hourly_pressure) >= 4:
                pressure_drop_3h = hourly_pressure[0] - hourly_pressure[3]

            climate_image = get_climate_image(wmo_meta["category"], temp_c, precip_24h)

            hourly_forecast = []
            h_times = hourly.get("time", [])[:24]
            h_temps = hourly.get("temperature_2m", [])[:24]
            h_precips = hourly.get("precipitation", [])[:24]
            h_winds = hourly.get("wind_speed_10m", [])[:24]
            h_humidity = hourly.get("relative_humidity_2m", [])[:24]

            for i in range(len(h_times)):
                time_str = h_times[i].split("T")[1] if "T" in h_times[i] else h_times[i]
                hourly_forecast.append({
                    "time": time_str,
                    "temp": h_temps[i] if i < len(h_temps) else 0,
                    "precip": h_precips[i] if i < len(h_precips) else 0,
                    "wind": h_winds[i] if i < len(h_winds) else 0,
                    "humidity": h_humidity[i] if i < len(h_humidity) else 0
                })

            daily_forecast = []
            d_times = daily.get("time", [])[:7]
            d_codes = daily.get("weather_code", [])[:7]
            d_max_t = daily.get("temperature_2m_max", [])[:7]
            d_min_t = daily.get("temperature_2m_min", [])[:7]
            d_precip = daily.get("precipitation_sum", [])[:7]
            d_prob = daily.get("precipitation_probability_max", [])[:7]
            d_wind = daily.get("wind_speed_10m_max", [])[:7]

            for i in range(len(d_times)):
                code = d_codes[i] if i < len(d_codes) else 0
                code_meta = WMO_WEATHER_CODES.get(code, {"desc": "Clear", "icon": "☀️"})
                daily_forecast.append({
                    "date": d_times[i],
                    "temp_max": d_max_t[i] if i < len(d_max_t) else 0,
                    "temp_min": d_min_t[i] if i < len(d_min_t) else 0,
                    "precip_sum": d_precip[i] if i < len(d_precip) else 0,
                    "precip_prob": d_prob[i] if i < len(d_prob) else 0,
                    "wind_max": d_wind[i] if i < len(d_wind) else 0,
                    "weather_desc": code_meta["desc"],
                    "icon": code_meta["icon"]
                })

            return {
                "city": city_name or "Custom Location",
                "country": country_name or "",
                "latitude": latitude,
                "longitude": longitude,
                "temperature": round(temp_c, 1),
                "feels_like": round(feels_like, 1),
                "humidity": round(humidity, 1),
                "precipitation": round(precip_24h, 1),
                "wind_speed": round(wind_speed, 1),
                "wind_gusts": round(wind_gusts, 1),
                "pressure": round(pressure, 1),
                "pressure_drop_3h": round(pressure_drop_3h, 2),
                "weather_code": wmo_code,
                "weather_desc": wmo_meta["desc"],
                "weather_category": wmo_meta["category"],
                "icon": wmo_meta["icon"],
                "climate_image": climate_image,
                "hourly": hourly_forecast,
                "daily": daily_forecast
            }
        else:
            print(f"Open-Meteo returned status {resp.status_code}, activating resilient fallback.")
            return generate_fallback_weather(latitude, longitude, city_name, country_name)
    except Exception as e:
        print(f"Weather fetch error: {e}, activating resilient fallback.")
        return generate_fallback_weather(latitude, longitude, city_name, country_name)

