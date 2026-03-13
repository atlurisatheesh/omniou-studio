"""
AGRISENSE — Weather & Pest Forecast Service
=============================================
Hyperlocal weather data + pest risk analysis based on weather conditions.
"""

import httpx
from datetime import datetime, timedelta

from ..config import settings


# ── Pest Risk Rules ──
# Temperature + Humidity conditions that trigger pest/disease outbreaks

PEST_WEATHER_RULES = [
    {
        "pest": "Rice Blast",
        "crops": ["rice"],
        "temp_min": 20, "temp_max": 30,
        "humidity_min": 85,
        "rain_trigger": True,
        "risk": "high",
        "advisory": "High blast risk. If not already applied, preventive spray of Tricyclazole 0.6g/L immediately. Scout fields daily.",
    },
    {
        "pest": "Brown Planthopper",
        "crops": ["rice"],
        "temp_min": 25, "temp_max": 35,
        "humidity_min": 80,
        "rain_trigger": False,
        "risk": "high",
        "advisory": "BPH conditions favorable. Avoid excess nitrogen. Drain water for 3 days. If ETL crossed (5-10/hill), apply Pymetrozine 50% WG @ 0.6g/L.",
    },
    {
        "pest": "Late Blight",
        "crops": ["tomato", "potato"],
        "temp_min": 10, "temp_max": 22,
        "humidity_min": 90,
        "rain_trigger": True,
        "risk": "critical",
        "advisory": "⚠️ CRITICAL: Late blight weather. Start preventive Mancozeb spray IMMEDIATELY. Repeat every 7 days. Check undersides of lower leaves for water-soaked spots.",
    },
    {
        "pest": "Yellow Rust",
        "crops": ["wheat"],
        "temp_min": 10, "temp_max": 20,
        "humidity_min": 70,
        "rain_trigger": False,
        "risk": "high",
        "advisory": "Yellow rust conditions. Scout for yellow stripes on leaves. If found, spray Propiconazole 1ml/L immediately.",
    },
    {
        "pest": "Fall Armyworm",
        "crops": ["maize"],
        "temp_min": 25, "temp_max": 38,
        "humidity_min": 60,
        "rain_trigger": False,
        "risk": "medium",
        "advisory": "Armyworm moth flight conditions. Check pheromone traps. Scout whorl leaves early morning for fresh frass.",
    },
    {
        "pest": "Whitefly (ToLCV vector)",
        "crops": ["tomato", "cotton"],
        "temp_min": 28, "temp_max": 40,
        "humidity_min": 40,
        "rain_trigger": False,
        "risk": "high",
        "advisory": "Hot dry conditions favor whitefly buildup. Check yellow sticky traps. Spray neem oil 5ml/L if populations increasing.",
    },
    {
        "pest": "Powdery Mildew",
        "crops": ["wheat", "tomato", "cotton"],
        "temp_min": 15, "temp_max": 28,
        "humidity_min": 60,
        "rain_trigger": False,
        "risk": "medium",
        "advisory": "Powdery mildew conditions. Avoid overhead irrigation. If white powdery spots seen, spray sulphur 80% WP @ 2.5g/L.",
    },
    {
        "pest": "Fruit Borer",
        "crops": ["tomato"],
        "temp_min": 20, "temp_max": 35,
        "humidity_min": 50,
        "rain_trigger": False,
        "risk": "medium",
        "advisory": "Monitor tomato fruits for bore holes. Install pheromone traps. Spray Emamectin benzoate if ETL crossed (1 larva/plant).",
    },
]


async def get_weather(lat: float, lon: float) -> dict:
    """
    Fetch current weather and 7-day forecast.
    Falls back to demo data if API key not configured.
    """
    if settings.WEATHER_API_KEY and settings.WEATHER_API_KEY != "your_openweathermap_api_key":
        return await _fetch_live_weather(lat, lon)
    return _demo_weather_data(lat, lon)


async def _fetch_live_weather(lat: float, lon: float) -> dict:
    """Fetch from OpenWeatherMap API."""
    async with httpx.AsyncClient(timeout=10) as client:
        # Current weather
        current_resp = await client.get(
            f"{settings.WEATHER_API_URL}/weather",
            params={"lat": lat, "lon": lon, "appid": settings.WEATHER_API_KEY, "units": "metric"},
        )
        current_resp.raise_for_status()
        current_data = current_resp.json()

        # 5-day forecast (free tier)
        forecast_resp = await client.get(
            f"{settings.WEATHER_API_URL}/forecast",
            params={"lat": lat, "lon": lon, "appid": settings.WEATHER_API_KEY, "units": "metric"},
        )
        forecast_resp.raise_for_status()
        forecast_data = forecast_resp.json()

    location = current_data.get("name", f"{lat:.2f}, {lon:.2f}")

    current = {
        "temp_c": current_data["main"]["temp"],
        "feels_like_c": current_data["main"]["feels_like"],
        "humidity_pct": current_data["main"]["humidity"],
        "wind_speed_kmh": round(current_data["wind"]["speed"] * 3.6, 1),
        "description": current_data["weather"][0]["description"].title(),
        "icon": current_data["weather"][0]["icon"],
        "rain_mm": current_data.get("rain", {}).get("1h", 0),
    }

    # Aggregate forecast by day
    daily = {}
    for item in forecast_data.get("list", []):
        date = item["dt_txt"][:10]
        if date not in daily:
            daily[date] = {"temps": [], "humidity": [], "rain": 0, "desc": "", "icon": ""}
        daily[date]["temps"].append(item["main"]["temp"])
        daily[date]["humidity"].append(item["main"]["humidity"])
        daily[date]["rain"] += item.get("rain", {}).get("3h", 0)
        daily[date]["desc"] = item["weather"][0]["description"].title()
        daily[date]["icon"] = item["weather"][0]["icon"]

    forecast = []
    for date, d in list(daily.items())[:7]:
        rain = round(d["rain"], 1)
        is_safe_to_spray = rain < 2 and max(d["humidity"]) < 85
        forecast.append({
            "date": date,
            "temp_min_c": round(min(d["temps"]), 1),
            "temp_max_c": round(max(d["temps"]), 1),
            "humidity_pct": round(sum(d["humidity"]) / len(d["humidity"])),
            "rain_mm": rain,
            "description": d["desc"],
            "icon": d["icon"],
            "spray_window": is_safe_to_spray,
            "spray_reason": "" if is_safe_to_spray else ("Rain expected" if rain >= 2 else "High humidity"),
        })

    # Calculate pest risks
    pest_risks = _evaluate_pest_risks(current["temp_c"], current["humidity_pct"], current["rain_mm"] > 0)

    return {
        "location": location,
        "current": current,
        "forecast": forecast,
        "pest_risks": pest_risks,
    }


def _demo_weather_data(lat: float, lon: float) -> dict:
    """Generate realistic demo weather data."""
    import random
    random.seed(int(lat * 100 + lon * 10))

    base_temp = 28 + random.uniform(-5, 8)
    base_humidity = 65 + random.uniform(-15, 25)

    current = {
        "temp_c": round(base_temp, 1),
        "feels_like_c": round(base_temp + 2, 1),
        "humidity_pct": round(base_humidity),
        "wind_speed_kmh": round(random.uniform(5, 25), 1),
        "description": random.choice(["Partly Cloudy", "Clear Sky", "Scattered Clouds", "Light Rain", "Haze"]),
        "icon": "02d",
        "rain_mm": round(random.uniform(0, 5), 1) if random.random() > 0.6 else 0,
    }

    today = datetime.utcnow()
    forecast = []
    for i in range(7):
        date = today + timedelta(days=i + 1)
        rain = round(random.uniform(0, 15), 1) if random.random() > 0.5 else 0
        humidity = round(base_humidity + random.uniform(-10, 10))
        is_safe = rain < 2 and humidity < 85
        forecast.append({
            "date": date.strftime("%Y-%m-%d"),
            "temp_min_c": round(base_temp - random.uniform(3, 8), 1),
            "temp_max_c": round(base_temp + random.uniform(2, 6), 1),
            "humidity_pct": humidity,
            "rain_mm": rain,
            "description": random.choice(["Sunny", "Cloudy", "Light Rain", "Partly Cloudy", "Thunderstorm"]),
            "icon": "02d",
            "spray_window": is_safe,
            "spray_reason": "" if is_safe else ("Rain expected" if rain >= 2 else "High humidity"),
        })

    pest_risks = _evaluate_pest_risks(current["temp_c"], current["humidity_pct"], current["rain_mm"] > 0)

    return {
        "location": f"Location ({lat:.2f}°N, {lon:.2f}°E)",
        "current": current,
        "forecast": forecast,
        "pest_risks": pest_risks,
    }


def _evaluate_pest_risks(temp: float, humidity: float, is_raining: bool) -> list[dict]:
    """Evaluate pest risks based on current weather conditions."""
    risks = []
    for rule in PEST_WEATHER_RULES:
        temp_match = rule["temp_min"] <= temp <= rule["temp_max"]
        humidity_match = humidity >= rule["humidity_min"]
        rain_check = not rule["rain_trigger"] or is_raining

        if temp_match and humidity_match and rain_check:
            risks.append({
                "pest": rule["pest"],
                "crops": rule["crops"],
                "risk": rule["risk"],
                "advisory": rule["advisory"],
            })

    return risks
