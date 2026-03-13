"""
AGRISENSE — Market Price Service
==================================
Commodity market prices, trends, and best market recommendations.
"""

import random
from datetime import datetime, timedelta

# ── Commodity Database with Realistic Price Ranges ──
COMMODITIES = {
    "rice": {
        "display": "Rice (Paddy)",
        "unit": "₹/quintal",
        "msp_2025": 2300,  # Minimum Support Price
        "price_range": (1800, 3200),
        "markets": [
            {"name": "Azadpur Mandi", "state": "Delhi", "district": "New Delhi"},
            {"name": "Kurnool", "state": "Andhra Pradesh", "district": "Kurnool"},
            {"name": "Warangal", "state": "Telangana", "district": "Warangal"},
            {"name": "Raipur", "state": "Chhattisgarh", "district": "Raipur"},
            {"name": "Karnal", "state": "Haryana", "district": "Karnal"},
            {"name": "Ludhiana", "state": "Punjab", "district": "Ludhiana"},
        ],
    },
    "wheat": {
        "display": "Wheat",
        "unit": "₹/quintal",
        "msp_2025": 2275,
        "price_range": (2000, 3500),
        "markets": [
            {"name": "Azadpur", "state": "Delhi", "district": "New Delhi"},
            {"name": "Indore", "state": "Madhya Pradesh", "district": "Indore"},
            {"name": "Karnal", "state": "Haryana", "district": "Karnal"},
            {"name": "Ludhiana", "state": "Punjab", "district": "Ludhiana"},
            {"name": "Hapur", "state": "Uttar Pradesh", "district": "Hapur"},
        ],
    },
    "tomato": {
        "display": "Tomato",
        "unit": "₹/quintal",
        "msp_2025": None,
        "price_range": (500, 8000),
        "markets": [
            {"name": "Kolar", "state": "Karnataka", "district": "Kolar"},
            {"name": "Madanapalle", "state": "Andhra Pradesh", "district": "Annamayya"},
            {"name": "Nashik", "state": "Maharashtra", "district": "Nashik"},
            {"name": "Azadpur", "state": "Delhi", "district": "New Delhi"},
            {"name": "Vashi", "state": "Maharashtra", "district": "Mumbai"},
        ],
    },
    "cotton": {
        "display": "Cotton (Kapas)",
        "unit": "₹/quintal",
        "msp_2025": 7121,
        "price_range": (5500, 9000),
        "markets": [
            {"name": "Rajkot", "state": "Gujarat", "district": "Rajkot"},
            {"name": "Guntur", "state": "Andhra Pradesh", "district": "Guntur"},
            {"name": "Nagpur", "state": "Maharashtra", "district": "Nagpur"},
            {"name": "Adilabad", "state": "Telangana", "district": "Adilabad"},
            {"name": "Bathinda", "state": "Punjab", "district": "Bathinda"},
        ],
    },
    "potato": {
        "display": "Potato",
        "unit": "₹/quintal",
        "msp_2025": None,
        "price_range": (400, 2500),
        "markets": [
            {"name": "Agra", "state": "Uttar Pradesh", "district": "Agra"},
            {"name": "Farrukhabad", "state": "Uttar Pradesh", "district": "Farrukhabad"},
            {"name": "Hooghly", "state": "West Bengal", "district": "Hooghly"},
            {"name": "Jalandhar", "state": "Punjab", "district": "Jalandhar"},
            {"name": "Indore", "state": "Madhya Pradesh", "district": "Indore"},
        ],
    },
    "onion": {
        "display": "Onion",
        "unit": "₹/quintal",
        "msp_2025": None,
        "price_range": (600, 6000),
        "markets": [
            {"name": "Lasalgaon", "state": "Maharashtra", "district": "Nashik"},
            {"name": "Pimpalgaon", "state": "Maharashtra", "district": "Nashik"},
            {"name": "Azadpur", "state": "Delhi", "district": "New Delhi"},
            {"name": "Bangalore", "state": "Karnataka", "district": "Bangalore"},
            {"name": "Mahuva", "state": "Gujarat", "district": "Bhavnagar"},
        ],
    },
    "soybean": {
        "display": "Soybean",
        "unit": "₹/quintal",
        "msp_2025": 4892,
        "price_range": (3800, 6500),
        "markets": [
            {"name": "Indore", "state": "Madhya Pradesh", "district": "Indore"},
            {"name": "Khandwa", "state": "Madhya Pradesh", "district": "Khandwa"},
            {"name": "Latur", "state": "Maharashtra", "district": "Latur"},
            {"name": "Nagpur", "state": "Maharashtra", "district": "Nagpur"},
        ],
    },
    "maize": {
        "display": "Maize",
        "unit": "₹/quintal",
        "msp_2025": 2090,
        "price_range": (1500, 2800),
        "markets": [
            {"name": "Davangere", "state": "Karnataka", "district": "Davangere"},
            {"name": "Gulbarga", "state": "Karnataka", "district": "Kalaburagi"},
            {"name": "Nizamabad", "state": "Telangana", "district": "Nizamabad"},
            {"name": "Aurangabad", "state": "Bihar", "district": "Aurangabad"},
        ],
    },
    "sugarcane": {
        "display": "Sugarcane",
        "unit": "₹/quintal",
        "msp_2025": 340,  # FRP
        "price_range": (280, 450),
        "markets": [
            {"name": "Muzaffarnagar", "state": "Uttar Pradesh", "district": "Muzaffarnagar"},
            {"name": "Kolhapur", "state": "Maharashtra", "district": "Kolhapur"},
            {"name": "Belgaum", "state": "Karnataka", "district": "Belgaum"},
            {"name": "Coimbatore", "state": "Tamil Nadu", "district": "Coimbatore"},
        ],
    },
    "groundnut": {
        "display": "Groundnut",
        "unit": "₹/quintal",
        "msp_2025": 6377,
        "price_range": (4800, 8000),
        "markets": [
            {"name": "Rajkot", "state": "Gujarat", "district": "Rajkot"},
            {"name": "Junagadh", "state": "Gujarat", "district": "Junagadh"},
            {"name": "Anantapur", "state": "Andhra Pradesh", "district": "Anantapur"},
            {"name": "Villupuram", "state": "Tamil Nadu", "district": "Villupuram"},
        ],
    },
}


def get_market_prices(commodity: str, state: str | None = None) -> dict:
    """
    Get market prices for a commodity.
    In production: fetches from data.gov.in API or agmarknet.
    Current: generates realistic simulated data.
    """
    key = commodity.lower()
    if key not in COMMODITIES:
        key = "rice"

    info = COMMODITIES[key]
    low, high = info["price_range"]

    prices = []
    best_price = 0
    best_market = ""

    for market in info["markets"]:
        if state and market["state"].lower() != state.lower():
            continue

        base = random.uniform(low, high)
        min_p = round(base * 0.92)
        max_p = round(base * 1.08)
        modal = round(base)

        # Calculate trend
        trend_pct = round(random.uniform(-8, 12), 1)
        trend = "up" if trend_pct > 2 else ("down" if trend_pct < -2 else "stable")

        prices.append({
            "commodity": info["display"],
            "market_name": market["name"],
            "state": market["state"],
            "district": market["district"],
            "min_price": min_p,
            "max_price": max_p,
            "modal_price": modal,
            "arrival_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "trend": trend,
            "trend_pct": trend_pct,
        })

        if modal > best_price:
            best_price = modal
            best_market = f"{market['name']}, {market['district']}"

    avg_price = round(sum(p["modal_price"] for p in prices) / max(len(prices), 1))

    # 7-day trend analysis
    trend_7d = random.choice(["up", "down", "stable"])
    msp = info["msp_2025"]
    msp_text = f"MSP ₹{msp}/quintal" if msp else "No MSP (market-driven)"

    return {
        "commodity": info["display"],
        "prices": prices,
        "avg_price": avg_price,
        "best_market": best_market,
        "price_trend_7d": trend_7d,
        "msp": msp_text,
        "advisory": _price_advisory(avg_price, msp, trend_7d),
    }


def _price_advisory(avg: float, msp: int | None, trend: str) -> str:
    """Generate selling advisory based on price and trend."""
    if msp and avg < msp:
        return f"⚠️ Market price (₹{avg}) is BELOW MSP (₹{msp}). Sell at government procurement center or store and wait."

    if trend == "up":
        return f"📈 Prices trending UP. Consider holding for 5-7 more days for better returns. Current avg: ₹{avg}/quintal."
    elif trend == "down":
        return f"📉 Prices declining. Consider selling soon at the best available market. Current avg: ₹{avg}/quintal."
    else:
        return f"➡️ Prices stable at ₹{avg}/quintal. Good time to sell if storage costs are high."


def get_supported_commodities() -> list[dict]:
    """List all supported commodities."""
    return [
        {
            "key": key,
            "name": info["display"],
            "msp": info["msp_2025"],
            "markets_count": len(info["markets"]),
        }
        for key, info in COMMODITIES.items()
    ]
