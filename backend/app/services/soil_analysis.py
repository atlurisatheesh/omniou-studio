"""
AGRISENSE — Soil Health Analysis Service
==========================================
Analyzes soil test parameters and generates fertilizer recommendations.
Uses ICAR-recommended ranges and crop-specific nutrient requirements.
"""

import json
from ..models.database import SoilTest
from sqlalchemy.ext.asyncio import AsyncSession


# ── Optimal Soil Parameter Ranges (ICAR Standards) ──

SOIL_RANGES = {
    "ph": {"low": (0, 5.5), "optimal": (5.5, 7.5), "high": (7.5, 14), "unit": ""},
    "nitrogen_kg_ha": {"low": (0, 280), "optimal": (280, 560), "high": (560, 2000), "unit": "kg/ha"},
    "phosphorus_kg_ha": {"low": (0, 25), "optimal": (25, 56), "high": (56, 500), "unit": "kg/ha"},
    "potassium_kg_ha": {"low": (0, 135), "optimal": (135, 335), "high": (335, 2000), "unit": "kg/ha"},
    "organic_carbon_pct": {"low": (0, 0.5), "optimal": (0.5, 0.75), "high": (0.75, 5), "unit": "%"},
    "ec_ds_m": {"low": (0, 0.8), "optimal": (0.8, 1.6), "high": (1.6, 10), "unit": "dS/m"},
    "zinc_ppm": {"low": (0, 0.6), "optimal": (0.6, 2.0), "high": (2.0, 50), "unit": "ppm"},
    "iron_ppm": {"low": (0, 4.5), "optimal": (4.5, 10), "high": (10, 100), "unit": "ppm"},
    "manganese_ppm": {"low": (0, 2.0), "optimal": (2.0, 5.0), "high": (5.0, 100), "unit": "ppm"},
    "boron_ppm": {"low": (0, 0.5), "optimal": (0.5, 1.0), "high": (1.0, 20), "unit": "ppm"},
    "sulphur_ppm": {"low": (0, 10), "optimal": (10, 20), "high": (20, 100), "unit": "ppm"},
}

# Crop-specific NPK requirements (kg/acre for general recommendation)
CROP_NUTRIENT_NEEDS = {
    "rice": {"N": 50, "P": 25, "K": 25, "note": "Apply N in 3 splits: basal, tillering, panicle initiation"},
    "wheat": {"N": 50, "P": 25, "K": 12, "note": "Apply N in 2 splits: basal + first irrigation"},
    "tomato": {"N": 40, "P": 30, "K": 30, "note": "Apply through drip fertigation if available"},
    "cotton": {"N": 32, "P": 16, "K": 16, "note": "Apply N in 3 splits up to flowering"},
    "potato": {"N": 50, "P": 40, "K": 40, "note": "Apply P and K as basal. N in 2 splits: planting + earthing up"},
    "maize": {"N": 48, "P": 24, "K": 16, "note": "Apply N in 3 splits: basal, knee-high, tasseling"},
    "sugarcane": {"N": 100, "P": 32, "K": 48, "note": "Apply N in 3-4 splits. K important for sugar content"},
    "soybean": {"N": 10, "P": 30, "K": 12, "note": "Low N due to nitrogen fixation. Rhizobium inoculation recommended"},
    "groundnut": {"N": 10, "P": 20, "K": 16, "note": "Apply gypsum @ 200kg/acre at pegging. Rhizobium seed treatment"},
}

NUTRIENT_NAMES = {
    "nitrogen_kg_ha": "Nitrogen (N)",
    "phosphorus_kg_ha": "Phosphorus (P)",
    "potassium_kg_ha": "Potassium (K)",
    "organic_carbon_pct": "Organic Carbon",
    "zinc_ppm": "Zinc (Zn)",
    "iron_ppm": "Iron (Fe)",
    "manganese_ppm": "Manganese (Mn)",
    "boron_ppm": "Boron (B)",
    "sulphur_ppm": "Sulphur (S)",
}

FERTILIZER_MAP = {
    "nitrogen_kg_ha": {"product": "Urea (46% N)", "factor": 2.17, "unit": "kg/acre"},
    "phosphorus_kg_ha": {"product": "DAP (18-46-0)", "factor": 2.17, "unit": "kg/acre"},
    "potassium_kg_ha": {"product": "MOP (60% K₂O)", "factor": 1.67, "unit": "kg/acre"},
    "zinc_ppm": {"product": "Zinc Sulphate (33% Zn)", "factor": 10, "unit": "kg/acre"},
    "iron_ppm": {"product": "Ferrous Sulphate", "factor": 8, "unit": "kg/acre"},
    "boron_ppm": {"product": "Borax", "factor": 4, "unit": "kg/acre"},
    "sulphur_ppm": {"product": "Bentonite Sulphur (90%)", "factor": 5, "unit": "kg/acre"},
}


def analyze_soil(data: dict, target_crop: str | None = None) -> dict:
    """
    Analyze soil test results and generate recommendations.

    Returns health score, deficiency details, and fertilizer recommendations.
    """
    deficiencies = []
    recommendations = []
    health_points = 0
    total_params = 0

    for param, ranges in SOIL_RANGES.items():
        value = data.get(param)
        if value is None:
            continue

        total_params += 1
        optimal = ranges["optimal"]
        unit = ranges["unit"]
        name = NUTRIENT_NAMES.get(param, param.replace("_", " ").title())

        if optimal[0] <= value <= optimal[1]:
            status = "optimal"
            health_points += 10
            rec_text = f"No additional {name.split('(')[0].strip()} needed"
            qty = "—"
        elif value < optimal[0]:
            status = "deficient"
            # Calculate deficit and fertilizer quantity
            deficit = optimal[0] - value
            fert = FERTILIZER_MAP.get(param)
            if fert:
                qty_val = round(deficit * fert["factor"], 1)
                qty = f"{qty_val} {fert['unit']} of {fert['product']}"
                rec_text = f"Apply {qty}"
            else:
                qty = "Consult agronomist"
                rec_text = f"{name} is deficient. Apply recommended amendment."

            if param == "ph":
                if value < 5.5:
                    qty = "Apply lime @ 2-4 quintals/acre"
                    rec_text = "Soil is acidic. Apply agricultural lime before sowing."
                health_points += 3
            elif param == "organic_carbon_pct":
                qty = "Apply FYM 4-5 tonnes/acre or vermicompost 2 tonnes/acre"
                rec_text = "Low organic matter. Add compost/FYM to build soil biology."
                health_points += 3
            else:
                health_points += 3
        else:
            status = "excess"
            health_points += 6

            if param == "ph" and value > 8.5:
                qty = "Apply gypsum @ 2-4 quintals/acre"
                rec_text = "Soil is alkaline. Apply gypsum to reduce pH."
            elif param == "ec_ds_m" and value > 4:
                qty = "Leaching irrigation + gypsum application"
                rec_text = "High salinity. Apply gypsum and ensure drainage."
            elif param == "nitrogen_kg_ha":
                qty = "Reduce urea application by 25%"
                rec_text = f"Excess {name}. Reduce nitrogen fertilizer to prevent crop lodging and environmental loss."
            else:
                qty = "Reduce application"
                rec_text = f"Excess {name}. Reduce further addition."

        deficiencies.append({
            "nutrient": name,
            "current_value": value,
            "optimal_range": f"{optimal[0]}-{optimal[1]} {unit}",
            "status": status,
            "recommendation": rec_text,
            "quantity_per_acre": qty,
        })

    # Overall health score (0-100)
    health_score = round((health_points / max(total_params * 10, 1)) * 100, 1) if total_params > 0 else 50

    # General recommendations
    if target_crop and target_crop.lower() in CROP_NUTRIENT_NEEDS:
        crop_info = CROP_NUTRIENT_NEEDS[target_crop.lower()]
        recommendations.append(f"For {target_crop.title()}: {crop_info['note']}")
        recommendations.append(
            f"Standard NPK for {target_crop.title()}: N={crop_info['N']}kg, P={crop_info['P']}kg, K={crop_info['K']}kg per acre. Adjust based on soil test."
        )

    # Universal recommendations
    oc = data.get("organic_carbon_pct") or 0.5
    if oc < 0.5:
        recommendations.append("🔴 Critical: Build organic carbon with green manuring (dhaincha/sunhemp), FYM, and crop residue incorporation.")

    ph = data.get("ph") or 7
    if ph < 5.5:
        recommendations.append("Apply lime 4-6 weeks before sowing for best results.")
    elif ph > 8.5:
        recommendations.append("Use acidifying fertilizers like ammonium sulphate instead of urea.")

    recommendations.append("Test soil every 2 seasons to track improvements. Take 10+ samples from field at 6-inch depth, mix, and send 500g.")

    return {
        "overall_health_score": health_score,
        "deficiencies": deficiencies,
        "recommendations": recommendations,
    }


async def save_soil_test(db: AsyncSession, data: dict, analysis: dict, user_id: str | None = None) -> str:
    """Save soil test and analysis results to database."""
    soil_test = SoilTest(
        user_id=user_id,
        ph=data.get("ph"),
        nitrogen_kg_ha=data.get("nitrogen_kg_ha"),
        phosphorus_kg_ha=data.get("phosphorus_kg_ha"),
        potassium_kg_ha=data.get("potassium_kg_ha"),
        organic_carbon_pct=data.get("organic_carbon_pct"),
        ec_ds_m=data.get("ec_ds_m"),
        zinc_ppm=data.get("zinc_ppm"),
        iron_ppm=data.get("iron_ppm"),
        manganese_ppm=data.get("manganese_ppm"),
        boron_ppm=data.get("boron_ppm"),
        sulphur_ppm=data.get("sulphur_ppm"),
        soil_type=data.get("soil_type"),
        target_crop=data.get("target_crop"),
        field_name=data.get("field_name"),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        fertilizer_recommendation=json.dumps(analysis["deficiencies"]),
        deficiency_alerts=json.dumps([d for d in analysis["deficiencies"] if d["status"] == "deficient"]),
        overall_health_score=analysis["overall_health_score"],
    )
    db.add(soil_test)
    await db.commit()
    await db.refresh(soil_test)
    return str(soil_test.id)
