"""
AGRISENSE — Crop Calendar Router
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import get_db
from ..models.schemas import CropCalendarCreate
from ..services.crop_calendar import generate_calendar, save_calendar, get_supported_crops

router = APIRouter(prefix="/calendar", tags=["Crop Calendar"])


@router.post("/create")
async def create_calendar(
    data: CropCalendarCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a smart crop calendar based on crop, variety, and sowing date."""
    calendar = generate_calendar(
        crop=data.crop,
        sowing_date=data.sowing_date,
        variety=data.variety,
        region=data.region,
    )

    calendar_id = await save_calendar(db, data.model_dump(), calendar)
    calendar["id"] = calendar_id

    return calendar


@router.get("/crops")
async def list_calendar_crops():
    """List crops with calendar support."""
    return {"crops": get_supported_crops()}


@router.get("/activities/{crop}")
async def get_crop_activities(crop: str):
    """Get full activity schedule for a crop."""
    from datetime import datetime
    calendar = generate_calendar(crop=crop, sowing_date=datetime.utcnow().strftime("%Y-%m-%d"))
    return {"crop": crop, "activities": calendar["activities"], "stages": calendar["stages"]}
