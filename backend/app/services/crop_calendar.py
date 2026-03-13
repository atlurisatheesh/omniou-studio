"""
AGRISENSE — Crop Calendar Service
===================================
Generate smart crop calendars with stage-wise activity schedules.
"""

import json
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.database import CropCalendar

# ── Crop Growth Stage Databases ──
# Days after sowing (DAS), stage, activities

CROP_CALENDARS = {
    "rice": {
        "duration_days": 120,
        "stages": [
            {"stage": "Nursery / Germination", "start": 0, "end": 21},
            {"stage": "Transplanting / Tillering", "start": 22, "end": 45},
            {"stage": "Active Tillering", "start": 46, "end": 60},
            {"stage": "Panicle Initiation", "start": 61, "end": 75},
            {"stage": "Flowering / Heading", "start": 76, "end": 90},
            {"stage": "Grain Filling", "start": 91, "end": 105},
            {"stage": "Maturity / Harvest", "start": 106, "end": 120},
        ],
        "activities": [
            {"day": 0, "activity": "Seed Treatment", "details": "Treat seeds with Carbendazim 2g/kg + Imidacloprid 5g/kg. Soak for 24 hours.", "type": "spray"},
            {"day": 1, "activity": "Nursery Sowing", "details": "Sow pre-germinated seeds on puddled nursery bed. Seed rate: 30kg/acre.", "type": "sowing"},
            {"day": 3, "activity": "Nursery Irrigation", "details": "Maintain thin film of water (2-3cm). Do not flood.", "type": "irrigation"},
            {"day": 10, "activity": "Nursery Weed Control", "details": "Hand weed or apply Pretilachlor 30.7% EC @ 600ml/acre in 3cm standing water.", "type": "spray"},
            {"day": 21, "activity": "Transplanting", "details": "Transplant 21-25 day old seedlings. Spacing: 20x15cm. 2-3 seedlings/hill.", "type": "sowing"},
            {"day": 22, "activity": "Basal Fertilizer", "details": "Apply DAP 50kg + MOP 25kg + ZnSO4 10kg per acre at transplanting.", "type": "fertilizer"},
            {"day": 28, "activity": "First Irrigation", "details": "Maintain 5cm standing water for weed suppression.", "type": "irrigation"},
            {"day": 30, "activity": "Herbicide Application", "details": "Apply Bispyribac sodium 10% SC @ 100ml/acre if weeds present. 3cm standing water required.", "type": "spray"},
            {"day": 35, "activity": "Scout for Pests", "details": "Check for stem borer dead hearts, BPH at base. Install pheromone traps.", "type": "scout"},
            {"day": 42, "activity": "First Top Dress (N)", "details": "Apply Urea 35kg/acre at active tillering stage. Drain field, apply, re-flood after 2 days.", "type": "fertilizer"},
            {"day": 50, "activity": "Scout for Diseases", "details": "Check for blast lesions, sheath blight. Brown spot on lower leaves.", "type": "scout"},
            {"day": 60, "activity": "Second Top Dress (N)", "details": "Apply Urea 25kg/acre at panicle initiation. This is critical for grain number.", "type": "fertilizer"},
            {"day": 65, "activity": "Preventive Spray", "details": "If blast-prone area: Tricyclazole 0.6g/L. If sheath blight: Hexaconazole 2ml/L.", "type": "spray"},
            {"day": 75, "activity": "Flowering Stage Care", "details": "Maintain 5cm water. DO NOT drain. Avoid any spraying during flowering. No nitrogen after this.", "type": "irrigation"},
            {"day": 85, "activity": "Grain Filling Check", "details": "Check for neck blast, grain discoloration. Spray Propiconazole 1ml/L if needed.", "type": "scout"},
            {"day": 100, "activity": "Drain Field", "details": "Stop irrigation 15-20 days before harvest. Allow field to dry naturally.", "type": "irrigation"},
            {"day": 115, "activity": "Harvest Readiness", "details": "Check grain moisture (20-22%). 80% panicles golden. Cut, thresh, dry to 14% moisture.", "type": "harvest"},
        ],
    },
    "wheat": {
        "duration_days": 140,
        "stages": [
            {"stage": "Germination", "start": 0, "end": 15},
            {"stage": "Seedling / Crown Root", "start": 16, "end": 30},
            {"stage": "Tillering", "start": 31, "end": 55},
            {"stage": "Jointing / Stem Extension", "start": 56, "end": 75},
            {"stage": "Heading / Flowering", "start": 76, "end": 95},
            {"stage": "Grain Filling / Dough", "start": 96, "end": 120},
            {"stage": "Maturity / Harvest", "start": 121, "end": 140},
        ],
        "activities": [
            {"day": 0, "activity": "Seed Treatment & Sowing", "details": "Treat with Carboxin+Thiram 3g/kg. Sow at 4-5cm depth. Seed rate: 40kg/acre. Row spacing: 20-22.5cm.", "type": "sowing"},
            {"day": 1, "activity": "Basal Fertilizer", "details": "Apply DAP 55kg + MOP 20kg + ZnSO4 10kg per acre at sowing.", "type": "fertilizer"},
            {"day": 3, "activity": "Pre-emergence Herbicide", "details": "Apply Pendimethalin 30% EC @ 1.3L/acre in 200L water before germination.", "type": "spray"},
            {"day": 21, "activity": "First Irrigation (CRI)", "details": "Crown Root Initiation — MOST CRITICAL irrigation. Do not miss. Light irrigation.", "type": "irrigation"},
            {"day": 22, "activity": "First Top Dress (N)", "details": "Immediately after first irrigation: Apply Urea 55kg/acre.", "type": "fertilizer"},
            {"day": 30, "activity": "Post-emergence Weed Control", "details": "If broadleaf weeds: 2,4-D 38% SL @ 500ml/acre. Grassy: Clodinafop 15% WP @ 160g/acre.", "type": "spray"},
            {"day": 42, "activity": "Second Irrigation", "details": "At tillering stage. Moderate irrigation.", "type": "irrigation"},
            {"day": 55, "activity": "Third Irrigation", "details": "At late jointing. Monitor for yellow rust from now.", "type": "irrigation"},
            {"day": 60, "activity": "Scout for Yellow Rust", "details": "Check leaves for yellow-orange stripes. If found: Propiconazole 1ml/L IMMEDIATELY.", "type": "scout"},
            {"day": 70, "activity": "Fourth Irrigation", "details": "At flowering stage. Critical for grain set.", "type": "irrigation"},
            {"day": 85, "activity": "Fifth Irrigation", "details": "Grain filling / milking stage.", "type": "irrigation"},
            {"day": 100, "activity": "Sixth Irrigation", "details": "Dough stage. Last irrigation. Avoid water stress here.", "type": "irrigation"},
            {"day": 110, "activity": "Scout for Karnal Bunt", "details": "Check for black powder in grains, fishy smell. Report to agriculture department.", "type": "scout"},
            {"day": 130, "activity": "Harvest Readiness", "details": "Check grain hardness — should not dent with thumbnail. Golden brown color. Moisture 12-14%. Avoid shattering by timely harvest.", "type": "harvest"},
        ],
    },
    "tomato": {
        "duration_days": 150,
        "stages": [
            {"stage": "Nursery", "start": 0, "end": 25},
            {"stage": "Transplanting / Establishment", "start": 26, "end": 40},
            {"stage": "Vegetative Growth", "start": 41, "end": 60},
            {"stage": "Flowering", "start": 61, "end": 80},
            {"stage": "Fruit Setting", "start": 81, "end": 100},
            {"stage": "Fruit Development", "start": 101, "end": 130},
            {"stage": "Harvesting", "start": 131, "end": 150},
        ],
        "activities": [
            {"day": 0, "activity": "Nursery Sowing", "details": "Sow in pro-trays or raised beds under shade net. Treat seeds with Thiram 3g/kg. Seed rate: 150g/acre.", "type": "sowing"},
            {"day": 15, "activity": "Nursery Spray", "details": "Spray Imidacloprid 0.3ml/L to protect from whitefly in nursery. Use 40-mesh net.", "type": "spray"},
            {"day": 25, "activity": "Transplanting", "details": "Transplant to main field. Spacing: 60x45cm. Apply FYM 4 tonnes/acre. Drip + mulch recommended.", "type": "sowing"},
            {"day": 26, "activity": "Basal Fertilizer", "details": "Apply 19:19:19 complex 50kg + SSP 100kg + MOP 30kg per acre. Mix in planting pits.", "type": "fertilizer"},
            {"day": 30, "activity": "Staking", "details": "Install bamboo or wire stakes. Train plants upward. Remove side shoots below first cluster.", "type": "scout"},
            {"day": 35, "activity": "First Fertigation", "details": "Start NPK 19:19:19 through drip @ 5kg/acre/week. Alternate with calcium nitrate.", "type": "fertilizer"},
            {"day": 40, "activity": "Scout — Whitefly & Virus", "details": "Check for leaf curl, yellowing, stunting (ToLCV symptoms). Remove infected plants IMMEDIATELY.", "type": "scout"},
            {"day": 50, "activity": "Preventive Fungicide", "details": "Spray Mancozeb 2.5g/L as preventive for early blight. Repeat every 14 days.", "type": "spray"},
            {"day": 55, "activity": "Micronutrient Spray", "details": "Foliar spray: Boron 1g/L + Calcium 3g/L for better fruit set and to prevent blossom end rot.", "type": "fertilizer"},
            {"day": 65, "activity": "Flowering Care", "details": "Maintain consistent moisture. Avoid water stress — causes flower drop. Spray 2,4-D 10ppm if poor fruit set.", "type": "irrigation"},
            {"day": 80, "activity": "Fruit Borer Scout", "details": "Check fruits for bore holes. Install Helicoverpa pheromone traps. If ETL crossed: Emamectin 0.4g/L.", "type": "scout"},
            {"day": 90, "activity": "Potash Application", "details": "Increase K through drip: SOP 5kg/acre/week. Improves fruit color, shelf life, sugar content.", "type": "fertilizer"},
            {"day": 100, "activity": "Late Blight Watch", "details": "If cool + wet: spray Cymoxanil+Mancozeb 3g/L preventively. Check daily.", "type": "scout"},
            {"day": 120, "activity": "First Harvest", "details": "Harvest at breaker stage (pink blush) for market. Full red for processing. Handle gently.", "type": "harvest"},
            {"day": 130, "activity": "Continue Harvest", "details": "Pick every 3-4 days. Grade by size. Avoid harvesting wet fruits — reduces shelf life.", "type": "harvest"},
        ],
    },
    "cotton": {
        "duration_days": 180,
        "stages": [
            {"stage": "Germination", "start": 0, "end": 15},
            {"stage": "Seedling", "start": 16, "end": 35},
            {"stage": "Squaring", "start": 36, "end": 60},
            {"stage": "Flowering", "start": 61, "end": 90},
            {"stage": "Boll Development", "start": 91, "end": 130},
            {"stage": "Boll Opening", "start": 131, "end": 160},
            {"stage": "Picking", "start": 161, "end": 180},
        ],
        "activities": [
            {"day": 0, "activity": "Sowing + Seed Treatment", "details": "Bt cotton: 1 packet/acre. Treat with Imidacloprid 70% WS @ 5g/kg. Row spacing: 90x60cm.", "type": "sowing"},
            {"day": 1, "activity": "Basal Fertilizer", "details": "Apply DAP 50kg + MOP 25kg + SSP 50kg per acre. Place 5cm away from seed.", "type": "fertilizer"},
            {"day": 15, "activity": "Gap Filling", "details": "Re-sow in gaps. Maintain 1 plant/hill. Thin overcrowded spots.", "type": "scout"},
            {"day": 25, "activity": "First Top Dress", "details": "Apply Urea 25kg/acre. Ring application around plant base.", "type": "fertilizer"},
            {"day": 30, "activity": "Interculture + Weed Control", "details": "Mechanical weeding between rows. Hand weeding within rows. Or Quizalofop 50ml/acre for grassy weeds.", "type": "spray"},
            {"day": 40, "activity": "Second Top Dress + Scout", "details": "Urea 25kg/acre. Scout for jassids, aphids on leaf undersides.", "type": "fertilizer"},
            {"day": 50, "activity": "Sucking Pest Management", "details": "If jassid/aphid above ETL: Flonicamid 50% WG @ 0.3g/L or neem oil 5ml/L.", "type": "spray"},
            {"day": 60, "activity": "Square Formation", "details": "Ensure adequate irrigation. Install bollworm pheromone traps. Begin weekly scouting.", "type": "scout"},
            {"day": 75, "activity": "Bollworm Monitoring", "details": "Check traps for moth catch. Scout 20 plants randomly. If >1 larva/plant: spray immediately.", "type": "scout"},
            {"day": 80, "activity": "Bollworm Spray", "details": "If needed: Emamectin benzoate 0.4g/L or Chlorantraniliprole 0.3ml/L. Spray in evening.", "type": "spray"},
            {"day": 90, "activity": "Third Top Dress", "details": "Apply MOP 20kg/acre for boll development. Potash crucial now.", "type": "fertilizer"},
            {"day": 100, "activity": "Pink Bollworm Watch", "details": "Check for rosette flowers (petals stuck). Mass trapping with PBW lures. Spray if ETL crossed.", "type": "scout"},
            {"day": 130, "activity": "Defoliant Decision", "details": "If machine picking: apply defoliant. If hand picking: let bolls open naturally.", "type": "spray"},
            {"day": 150, "activity": "First Picking", "details": "Pick when 60% bolls open. Pick only fully opened bolls. Avoid contamination — no polypropylene bags.", "type": "harvest"},
            {"day": 170, "activity": "Second Picking", "details": "Remaining bolls. Grade: clean picked vs. last pick. Destroy stalks within 15 days of final pick.", "type": "harvest"},
        ],
    },
    "potato": {
        "duration_days": 100,
        "stages": [
            {"stage": "Sprouting / Emergence", "start": 0, "end": 20},
            {"stage": "Vegetative Growth", "start": 21, "end": 40},
            {"stage": "Tuber Initiation", "start": 41, "end": 55},
            {"stage": "Tuber Bulking", "start": 56, "end": 80},
            {"stage": "Maturity / Harvest", "start": 81, "end": 100},
        ],
        "activities": [
            {"day": 0, "activity": "Planting", "details": "Plant pre-sprouted tubers (2-3 sprouts). Seed rate: 8-10 quintals/acre. Spacing: 60x20cm. Depth: 5-7cm.", "type": "sowing"},
            {"day": 1, "activity": "Basal Fertilizer", "details": "Apply DAP 75kg + MOP 50kg + ZnSO4 10kg per acre in furrows before planting.", "type": "fertilizer"},
            {"day": 5, "activity": "First Irrigation", "details": "Light irrigation for uniform emergence. Do not flood.", "type": "irrigation"},
            {"day": 20, "activity": "First Earthing Up + N", "details": "Earthing up at 20 DAS. Apply Urea 50kg/acre along ridges. Covers exposed tubers.", "type": "fertilizer"},
            {"day": 30, "activity": "Second Irrigation", "details": "Maintain moderate moisture. Avoid water stress — causes knobby tubers.", "type": "irrigation"},
            {"day": 35, "activity": "Second Earthing Up", "details": "Final earthing up. Ensure all tubers well covered. Prevents greening.", "type": "scout"},
            {"day": 40, "activity": "Late Blight Preventive", "details": "Start Mancozeb 2.5g/L PREVENTIVE spray. If cool+wet: use Cymoxanil+Mancozeb 3g/L. Repeat every 7-10 days.", "type": "spray"},
            {"day": 55, "activity": "Tuber Bulking Irrigation", "details": "Critical moisture period. Irrigate every 7-10 days. Uneven watering causes growth cracks.", "type": "irrigation"},
            {"day": 70, "activity": "Stop Nitrogen", "details": "No more nitrogen. Continue potash through drip if available for tuber size.", "type": "fertilizer"},
            {"day": 85, "activity": "Haulm Cutting", "details": "Cut haulms (above-ground growth) 10-15 days before harvest. Helps skin hardening. Prevents late blight reaching tubers.", "type": "harvest"},
            {"day": 95, "activity": "Harvest", "details": "Dig carefully to avoid cuts. Grade by size. Cure in shade 3-5 days. Store at 2-4°C for table, 15-20°C for seed.", "type": "harvest"},
        ],
    },
    "maize": {
        "duration_days": 110,
        "stages": [
            {"stage": "Germination / Emergence", "start": 0, "end": 12},
            {"stage": "Seedling (V1-V6)", "start": 13, "end": 30},
            {"stage": "Rapid Growth (V7-VT)", "start": 31, "end": 55},
            {"stage": "Tasseling / Silking", "start": 56, "end": 70},
            {"stage": "Grain Filling", "start": 71, "end": 95},
            {"stage": "Maturity / Harvest", "start": 96, "end": 110},
        ],
        "activities": [
            {"day": 0, "activity": "Sowing", "details": "Sow at 5cm depth. Spacing: 60x20cm. Seed rate: 8kg/acre. Treat with Thiamethoxam 30% FS @ 8ml/kg.", "type": "sowing"},
            {"day": 1, "activity": "Basal Fertilizer", "details": "Apply DAP 55kg + MOP 30kg per acre. Band placement 5cm away from seed.", "type": "fertilizer"},
            {"day": 3, "activity": "Pre-emergence Herbicide", "details": "Atrazine 50% WP @ 500g/acre in 200L water. Apply on moist soil before germination.", "type": "spray"},
            {"day": 15, "activity": "Thinning + Scout", "details": "Thin to 1 plant/hill. Check for fall armyworm — look in whorls for frass early morning.", "type": "scout"},
            {"day": 25, "activity": "First Top Dress", "details": "Apply Urea 45kg/acre at knee-high (V6) stage. Side dress in furrows.", "type": "fertilizer"},
            {"day": 30, "activity": "Armyworm Management", "details": "If frass found: Apply Emamectin 0.4g/L or sand+lime (9:1) into whorls. Spray in evening only.", "type": "spray"},
            {"day": 45, "activity": "Second Top Dress", "details": "Apply Urea 35kg/acre at pre-tasseling. Last nitrogen application.", "type": "fertilizer"},
            {"day": 50, "activity": "Irrigation", "details": "Critical moisture needed. Tasseling and silking — most water-sensitive stages. Irrigate if dry.", "type": "irrigation"},
            {"day": 60, "activity": "Pollination Period", "details": "DO NOT spray insecticides during tasseling — kills pollinators. Ensure adequate moisture.", "type": "scout"},
            {"day": 75, "activity": "Cob Development", "details": "Check for cob borer damage. Maintain moisture for grain filling.", "type": "scout"},
            {"day": 95, "activity": "Maturity Check", "details": "Black layer at grain base indicates maturity. Husk drying. Grain moisture 25-30%.", "type": "scout"},
            {"day": 105, "activity": "Harvest", "details": "Harvest when moisture 20-25%. Shell and dry to 12-13%. Early harvest avoids storage pests.", "type": "harvest"},
        ],
    },
}


def generate_calendar(crop: str, sowing_date: str, variety: str | None = None, region: str | None = None) -> dict:
    """Generate complete crop calendar with activities."""
    crop_key = crop.lower()
    if crop_key not in CROP_CALENDARS:
        # Fallback to generic calendar
        crop_key = "rice"

    calendar = CROP_CALENDARS[crop_key]
    sow_dt = datetime.fromisoformat(sowing_date)
    harvest_dt = sow_dt + timedelta(days=calendar["duration_days"])

    # Determine current stage
    days_elapsed = (datetime.utcnow() - sow_dt).days
    current_stage = "Not yet sown"
    for stage in calendar["stages"]:
        if stage["start"] <= days_elapsed <= stage["end"]:
            current_stage = stage["stage"]
            break
    if days_elapsed > calendar["duration_days"]:
        current_stage = "Harvested"
    elif days_elapsed < 0:
        current_stage = f"Sowing in {abs(days_elapsed)} days"

    # Build activity list with actual dates
    activities = []
    for act in calendar["activities"]:
        act_date = sow_dt + timedelta(days=act["day"])
        activities.append({
            "day": act["day"],
            "date": act_date.strftime("%Y-%m-%d"),
            "stage": _get_stage_for_day(act["day"], calendar["stages"]),
            "activity": act["activity"],
            "details": act["details"],
            "type": act["type"],
            "is_past": act_date < datetime.utcnow(),
            "is_today": act_date.date() == datetime.utcnow().date(),
            "is_upcoming": 0 <= (act_date - datetime.utcnow()).days <= 7,
        })

    return {
        "crop": crop,
        "variety": variety,
        "sowing_date": sowing_date,
        "expected_harvest_date": harvest_dt.strftime("%Y-%m-%d"),
        "current_stage": current_stage,
        "days_elapsed": max(days_elapsed, 0),
        "total_days": calendar["duration_days"],
        "stages": calendar["stages"],
        "activities": activities,
    }


def _get_stage_for_day(day: int, stages: list[dict]) -> str:
    for stage in stages:
        if stage["start"] <= day <= stage["end"]:
            return stage["stage"]
    return "Unknown"


async def save_calendar(db: AsyncSession, data: dict, calendar: dict, user_id: str | None = None) -> str:
    """Save crop calendar to database."""
    entry = CropCalendar(
        user_id=user_id,
        crop=data["crop"],
        variety=data.get("variety"),
        sowing_date=datetime.fromisoformat(data["sowing_date"]),
        expected_harvest_date=datetime.fromisoformat(calendar["expected_harvest_date"]),
        field_name=data.get("field_name"),
        field_size_acres=data.get("field_size_acres"),
        region=data.get("region"),
        current_stage=calendar["current_stage"],
        activities_json=json.dumps(calendar["activities"]),
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return str(entry.id)


def get_supported_crops() -> list[dict]:
    """List crops with calendar support."""
    return [
        {
            "name": crop,
            "duration_days": data["duration_days"],
            "stages_count": len(data["stages"]),
            "activities_count": len(data["activities"]),
        }
        for crop, data in CROP_CALENDARS.items()
    ]
