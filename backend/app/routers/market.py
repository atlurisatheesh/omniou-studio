"""
AGRISENSE — Market Prices Router
"""

from fastapi import APIRouter

from ..services.market_service import get_market_prices, get_supported_commodities

router = APIRouter(prefix="/market", tags=["Market Prices"])


@router.get("/prices/{commodity}")
async def market_prices(commodity: str, state: str | None = None):
    """Get market prices for a commodity across mandis."""
    data = get_market_prices(commodity, state)
    return data


@router.get("/commodities")
async def list_commodities():
    """List all supported commodities."""
    return {"commodities": get_supported_commodities()}


@router.get("/advisory/{commodity}")
async def price_advisory(commodity: str):
    """Get buy/sell advisory for a commodity."""
    data = get_market_prices(commodity)
    return {
        "commodity": data["commodity"],
        "avg_price": data["avg_price"],
        "trend": data["price_trend_7d"],
        "best_market": data["best_market"],
        "advisory": data["advisory"],
        "msp": data.get("msp"),
    }
