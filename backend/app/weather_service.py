from datetime import date, timedelta
from typing import Any
import os
import httpx
from fastapi import HTTPException

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "").strip()


def _optional_headers() -> dict[str, str]:
    # Open-Meteo needs no API key; this keeps provider migration simple.
    if WEATHER_API_KEY:
        return {
            "Authorization": f"Bearer {WEATHER_API_KEY}",
            "X-API-Key": WEATHER_API_KEY,
        }
    return {}


async def resolve_location(location: str) -> dict[str, Any]:
    raw = location.strip()
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) == 2:
        try:
            latitude = float(parts[0])
            longitude = float(parts[1])
        except ValueError:
            latitude = None
            longitude = None
        if latitude is not None and longitude is not None:
            if not (-90 <= latitude <= 90):
                raise HTTPException(status_code=400, detail="Latitude must be between -90 and 90")
            if not (-180 <= longitude <= 180):
                raise HTTPException(status_code=400, detail="Longitude must be between -180 and 180")
            return {
                "resolved_location": f"{latitude:.4f}, {longitude:.4f}",
                "latitude": latitude,
                "longitude": longitude,
            }

    params = {"name": raw, "count": 1, "language": "en", "format": "json"}
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(GEOCODE_URL, params=params, headers=_optional_headers())
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Failed to resolve location via geocoding API")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to resolve location via geocoding API")

    data = response.json()
    results = data.get("results") or []
    if not results:
        raise HTTPException(status_code=404, detail="Location could not be resolved")

    item = results[0]
    name = item.get("name", "Unknown")
    admin1 = item.get("admin1")
    country = item.get("country", "")
    resolved_name = ", ".join([part for part in [name, admin1, country] if part])

    return {
        "resolved_location": resolved_name,
        "latitude": item["latitude"],
        "longitude": item["longitude"],
    }


def _ensure_valid_date_range(start_date: date, end_date: date):
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Start date cannot be after end date")


async def fetch_current_weather(latitude: float, longitude: float) -> dict[str, Any]:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "timezone": "auto",
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(FORECAST_URL, params=params, headers=_optional_headers())
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Failed to fetch current weather")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch current weather")

    payload = response.json()
    current = payload.get("current", {})
    weather_code = current.get("weather_code")
    current["weather_condition"] = WEATHER_CODE_MAP.get(weather_code, "Unknown")
    return current


async def fetch_forecast(latitude: float, longitude: float, start_date: date, end_date: date) -> dict[str, Any]:
    _ensure_valid_date_range(start_date, end_date)
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,wind_speed_10m_max",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "timezone": "auto",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(FORECAST_URL, params=params, headers=_optional_headers())
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Failed to fetch forecast weather")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch forecast weather")

    payload = response.json()
    daily = payload.get("daily", {})
    codes = daily.get("weather_code", [])
    daily["weather_condition"] = [WEATHER_CODE_MAP.get(code, "Unknown") for code in codes]
    return daily


async def fetch_default_5_day_forecast(latitude: float, longitude: float) -> dict[str, Any]:
    start_date = date.today()
    end_date = start_date + timedelta(days=4)
    return await fetch_forecast(latitude, longitude, start_date, end_date)
