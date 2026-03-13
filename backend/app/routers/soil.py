"""
AGRISENSE — Soil Health Router
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import get_db
from ..models.schemas import SoilTestCreate
from ..services.soil_analysis import analyze_soil, save_soil_test

router = APIRouter(prefix="/soil", tags=["Soil Health"])


@router.post("/analyze")
async def analyze_soil_test(
    data: SoilTestCreate,
    db: AsyncSession = Depends(get_db),
):
    """Analyze soil test parameters and get fertilizer recommendations."""
    analysis = analyze_soil(data.model_dump(), target_crop=data.target_crop)
    test_id = await save_soil_test(db, data.model_dump(), analysis)

    return {
        "id": test_id,
        **analysis,
    }


@router.get("/ranges")
async def get_optimal_ranges():
    """Get ICAR-recommended optimal ranges for soil parameters."""
    from ..services.soil_analysis import SOIL_RANGES, NUTRIENT_NAMES

    ranges = []
    for param, values in SOIL_RANGES.items():
        name = NUTRIENT_NAMES.get(param, param.replace("_", " ").title())
        ranges.append({
            "parameter": param,
            "name": name,
            "low": f"< {values['optimal'][0]}",
            "optimal": f"{values['optimal'][0]} - {values['optimal'][1]}",
            "high": f"> {values['optimal'][1]}",
            "unit": values["unit"],
        })
    return {"ranges": ranges}


@router.get("/crop-needs")
async def get_crop_nutrient_needs():
    """Get NPK requirements by crop."""
    from ..services.soil_analysis import CROP_NUTRIENT_NEEDS

    return {
        "crops": [
            {"name": crop, **needs}
            for crop, needs in CROP_NUTRIENT_NEEDS.items()
        ]
    }
