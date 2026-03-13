"""
AGRISENSE — Weather & Pest Forecast Router
"""

from fastapi import APIRouter

from ..services.weather_service import get_weather

router = APIRouter(prefix="/weather", tags=["Weather & Pest Forecast"])


@router.get("/forecast")
async def weather_forecast(lat: float = 17.39, lon: float = 78.49):
    """
    Get weather forecast + pest risk analysis.
    Default: Hyderabad, India (17.39°N, 78.49°E)
    """
    data = await get_weather(lat, lon)
    return data


@router.get("/spray-window")
async def spray_window(lat: float = 17.39, lon: float = 78.49):
    """Get 7-day spray window analysis."""
    data = await get_weather(lat, lon)
    windows = []
    for day in data["forecast"]:
        windows.append({
            "date": day["date"],
            "safe_to_spray": day["spray_window"],
            "reason": day["spray_reason"],
            "rain_mm": day["rain_mm"],
            "humidity_pct": day["humidity_pct"],
        })
    return {"spray_windows": windows}
