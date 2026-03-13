"""
AGRISENSE — Disease Detection Service
======================================
Crop disease identification from leaf/plant images.
Uses a knowledge base for detection with confidence scoring.
In production, integrates with ONNX/TensorFlow models.
"""

import json
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import CropScan

# ── Disease Knowledge Base ──
# Comprehensive database of crop diseases with treatments
# In production: replaced by ML model inference

DISEASE_DATABASE = {
    "rice": [
        {
            "name": "Rice Blast (Magnaporthe oryzae)",
            "symptoms": ["diamond-shaped lesions", "gray center spots", "brown margins on leaves"],
            "severity_range": [3, 5],
            "chemical": "Apply Tricyclazole 75% WP @ 0.6g/L or Isoprothiolane 40% EC @ 1.5ml/L. Spray at tillering and panicle initiation stages.",
            "organic": "Apply Pseudomonas fluorescens @ 10g/L as foliar spray. Use Trichoderma viride enriched FYM @ 2.5kg/ha in nursery bed. Neem oil 3% spray.",
            "prevention": "Use resistant varieties (Pusa Basmati 1509, IR64). Avoid excess nitrogen. Maintain proper spacing. Drain standing water during dew formation periods. Seed treatment with Carbendazim 2g/kg.",
        },
        {
            "name": "Bacterial Leaf Blight (Xanthomonas oryzae)",
            "symptoms": ["yellow to white lesions along veins", "wavy leaf margins", "wilting"],
            "severity_range": [2, 4],
            "chemical": "Spray Streptomycin sulphate + Tetracycline (300ppm) or Copper oxychloride 50% WP @ 2.5g/L at 15-day intervals.",
            "organic": "Apply neem cake @ 150kg/ha. Spray Pseudomonas fluorescens @ 10g/L. Use fermented buttermilk spray (1:10 dilution).",
            "prevention": "Use certified disease-free seeds. Avoid clipping of seedling tips during transplanting. Balanced NPK fertilization. Drain excess water. Avoid irrigating from infected fields.",
        },
        {
            "name": "Sheath Blight (Rhizoctonia solani)",
            "symptoms": ["oval greenish-gray lesions on sheath", "irregular spots", "lodging"],
            "severity_range": [2, 4],
            "chemical": "Spray Validamycin 3% SL @ 2ml/L or Hexaconazole 5% SC @ 2ml/L. Apply at booting stage. Repeat after 15 days if needed.",
            "organic": "Apply Trichoderma harzianum @ 2.5kg/ha mixed with FYM. Spray Pseudomonas fluorescens @ 10g/L. Use neem oil 2% emulsion.",
            "prevention": "Avoid dense planting. Proper weed management. Remove crop residues after harvest. Crop rotation with legumes. Balanced fertilization — avoid excess nitrogen.",
        },
        {
            "name": "Brown Spot (Bipolaris oryzae)",
            "symptoms": ["small oval brown spots", "gray center on older lesions", "seed discoloration"],
            "severity_range": [1, 3],
            "chemical": "Spray Mancozeb 75% WP @ 2.5g/L or Propiconazole 25% EC @ 1ml/L. Apply at tillering and pre-flowering.",
            "organic": "Spray Pseudomonas fluorescens @ 10g/L. Apply neem oil 3%. Use Trichoderma enriched vermicompost.",
            "prevention": "Seed treatment with Thiram @ 2g/kg or Carbendazim @ 2g/kg. Use resistant varieties. Apply adequate potassium. Avoid moisture stress.",
        },
    ],
    "wheat": [
        {
            "name": "Yellow Rust (Puccinia striiformis)",
            "symptoms": ["yellow-orange stripes on leaves", "parallel to veins", "powdery pustules"],
            "severity_range": [3, 5],
            "chemical": "Spray Propiconazole 25% EC @ 1ml/L or Tebuconazole 25.9% EC @ 1ml/L. First spray at initial appearance, repeat after 15 days.",
            "organic": "Spray milk solution (1:9 ratio). Apply sulfur dust @ 25kg/ha. Neem oil 2% foliar spray.",
            "prevention": "Grow resistant varieties (HD 3226, DBW 187). Early sowing (before Nov 15). Avoid late nitrogen application. Monitor from January onwards.",
        },
        {
            "name": "Loose Smut (Ustilago tritici)",
            "symptoms": ["black powdery mass replacing grain", "exposed rachis", "early heading"],
            "severity_range": [3, 5],
            "chemical": "Seed treatment with Carboxin 75% WP @ 2g/kg or Tebuconazole 2% DS @ 1.5g/kg seed before sowing. No field spray effective.",
            "organic": "Hot water seed treatment at 52°C for 10 minutes. Solar seed treatment — soak seeds 4 hours, sun-dry on tarps for 4 hours.",
            "prevention": "Mandatory seed treatment. Use certified seeds from disease-free plots. Remove and destroy infected heads before spore release.",
        },
        {
            "name": "Karnal Bunt (Tilletia indica)",
            "symptoms": ["partial conversion of grain to black powder", "fishy smell", "black masses in grain"],
            "severity_range": [2, 4],
            "chemical": "Seed treatment with Thiram + Carboxin (1:1) @ 2.5g/kg. Foliar spray of Propiconazole 25% EC @ 1ml/L at heading.",
            "organic": "Neem seed kernel extract 5%. Hot water seed treatment 52°C for 10 min. Bio-agent Trichoderma viride seed treatment @ 4g/kg.",
            "prevention": "Use certified seed. Avoid late sowing. Deep ploughing in summer. Crop rotation. Avoid excess irrigation during heading.",
        },
    ],
    "tomato": [
        {
            "name": "Early Blight (Alternaria solani)",
            "symptoms": ["dark concentric rings on lower leaves", "target-board appearance", "defoliation"],
            "severity_range": [2, 4],
            "chemical": "Spray Mancozeb 75% WP @ 2.5g/L or Chlorothalonil 75% WP @ 2g/L. Start at first symptom, repeat every 10-14 days.",
            "organic": "Spray Trichoderma viride @ 5g/L. Apply baking soda solution (1 tbsp/gallon). Neem oil spray 2%. Compost tea foliar application.",
            "prevention": "3-year crop rotation (avoid solanaceous crops). Mulching to prevent soil splash. Stake plants for air circulation. Remove lower leaves touching ground. Drip irrigation — avoid wetting foliage.",
        },
        {
            "name": "Late Blight (Phytophthora infestans)",
            "symptoms": ["water-soaked dark lesions", "white fuzzy growth underneath", "rapid plant death"],
            "severity_range": [4, 5],
            "chemical": "Spray Metalaxyl 8% + Mancozeb 64% WP @ 2.5g/L or Cymoxanil 8% + Mancozeb 64% WP @ 3g/L. IMMEDIATELY on first sign. Repeat every 7 days in wet weather.",
            "organic": "Copper hydroxide spray @ 2g/L. Bordeaux mixture 1%. Remove and destroy all infected plant material. CANNOT be controlled organically in severe cases — act fast.",
            "prevention": "Plant resistant varieties (Arka Rakshak, Arka Abhed). Wide spacing for air flow. Avoid overhead irrigation. Never work in wet fields. Monitor after every rainfall. Eliminate volunteer plants.",
        },
        {
            "name": "Tomato Leaf Curl Virus (ToLCV)",
            "symptoms": ["upward leaf curling", "yellowing", "stunted growth", "small leaves"],
            "severity_range": [3, 5],
            "chemical": "NO chemical cure for virus. Control whitefly vector: Imidacloprid 17.8% SL @ 0.3ml/L or Thiamethoxam 25% WG @ 0.3g/L. Yellow sticky traps @ 12/acre.",
            "organic": "Neem oil 5ml/L spray every 7 days to repel whiteflies. Install yellow sticky traps. Companion planting with marigold as trap crop. Release Encarsia formosa (whitefly parasitoid).",
            "prevention": "Use ToLCV resistant varieties (Arka Ananya, TH-1). Raise nursery under 40-mesh nylon net. Remove and destroy infected plants immediately. Avoid whitefly-prone seasons. Barrier crops of 3-4 rows of maize/sorghum.",
        },
    ],
    "cotton": [
        {
            "name": "Cotton Bollworm (Helicoverpa armigera)",
            "symptoms": ["bore holes in bolls", "frass on bolls", "damaged squares and flowers"],
            "severity_range": [3, 5],
            "chemical": "Spray Emamectin benzoate 5% SG @ 0.4g/L or Chlorantraniliprole 18.5% SC @ 0.3ml/L. Apply when ETL crosses 1 larva/plant. Rotate insecticides.",
            "organic": "Release Trichogramma chilonis egg parasitoid @ 1.5 lakh/ha at 3 releases. Spray HaNPV (Helicoverpa Nuclear Polyhedrosis Virus) @ 250 LE/ha. Neem seed kernel extract 5%. Bird perches @ 20/acre.",
            "prevention": "Bt cotton varieties. Pheromone traps (Helilure) @ 5/acre for monitoring. Refugia — plant 20% non-Bt cotton as border. Intercrop with pigeon pea. Avoid monocropping. Deep summer ploughing.",
        },
        {
            "name": "Pink Bollworm (Pectinophora gossypiella)",
            "symptoms": ["rosette flowers", "interlocular burrowing in bolls", "stained lint"],
            "severity_range": [3, 5],
            "chemical": "Spray Quinalphos 25% EC @ 2ml/L or Profenophos 50% EC @ 2ml/L at first flush of flowers. Repeat at 15-day intervals.",
            "organic": "Mass trapping using PBW pheromone traps @ 5/acre. Release Trichogramma @ 1.5 lakh/ha. Neem oil 2% spray. Sterile insect technique where available.",
            "prevention": "Early and uniform sowing. Synchronous planting in community. Destroy crop residues by shredding/ploughing within 15 days of picking. Stack uprooted plants burnt. Avoid ratooning.",
        },
    ],
    "potato": [
        {
            "name": "Late Blight (Phytophthora infestans)",
            "symptoms": ["water-soaked patches", "brown-black lesions", "white mold underneath", "rapidly spreading"],
            "severity_range": [4, 5],
            "chemical": "Spray Cymoxanil 8% + Mancozeb 64% WP @ 3g/L or Dimethomorph 50% WP @ 1g/L. Start PREVENTIVE sprays when humidity >80% for 48 hours. Repeat every 7 days.",
            "organic": "Bordeaux mixture 1% preventive spray. Copper hydroxide @ 2g/L. Remove all infected foliage immediately. Destroy culled tubers — do NOT compost.",
            "prevention": "Plant resistant varieties (Kufri Jyoti, Kufri Girdhari). Certified disease-free seed tubers only. Hilling to prevent tuber exposure. DO NOT irrigate in evening — irrigate morning only. Destroy volunteer plants. 3+ year rotation from solanaceous crops.",
        },
    ],
    "maize": [
        {
            "name": "Fall Armyworm (Spodoptera frugiperda)",
            "symptoms": ["ragged feeding on whorl leaves", "frass in whorl", "windowpane feeding on young leaves"],
            "severity_range": [3, 5],
            "chemical": "Spray Emamectin benzoate 5% SG @ 0.4g/L or Spinetoram 11.7% SC @ 0.5ml/L directed into the whorl. Apply in evening only. Add sticker.",
            "organic": "Apply sand + lime powder (9:1) into whorls. Spray Metarhizium rileyi (Nomuraea rileyi) @ 10g/L. Release Telenomus remus (egg parasitoid). Spray neem oil 5% into whorl. Bt spray (Bacillus thuringiensis) @ 2g/L.",
            "prevention": "Early sowing (before June 15 for Kharif). Install pheromone traps @ 5/acre for monitoring. Intercrop with pigeon pea or cowpea. Erect bird perches @ 50/ha. Deep summer ploughing to expose pupae.",
        },
    ],
    "sugarcane": [
        {
            "name": "Red Rot (Colletotrichum falcatum)",
            "symptoms": ["drying of top leaves", "red internal stalk tissue", "white patches in red tissue", "alcohol smell"],
            "severity_range": [4, 5],
            "chemical": "No effective field spray. Sett treatment with Carbendazim 50% WP @ 2g/L for 15 minutes before planting. Hot water treatment 52°C for 30 minutes.",
            "organic": "Sett treatment with Trichoderma viride @ 10g/L for 15 minutes. Apply Pseudomonas fluorescens @ 10g/L soil drench at planting.",
            "prevention": "Use resistant varieties (Co 86032, CoC 671). Disease-free seed material ONLY. Avoid ratooning infected fields. Crop rotation with rice/pulses. Remove and burn infected stools. Drain waterlogged areas.",
        },
    ],
}

# Healthy crop signatures for baseline comparison
HEALTHY_BASELINES = {
    "rice": {"leaf_color": "dark green", "texture": "smooth", "tip_condition": "pointed and intact"},
    "wheat": {"leaf_color": "green to light green", "texture": "slightly rough", "tip_condition": "intact"},
    "tomato": {"leaf_color": "dark green", "texture": "slightly hairy", "tip_condition": "serrated, no curling"},
    "cotton": {"leaf_color": "green", "texture": "smooth with 3-5 lobes", "tip_condition": "broad, flat"},
    "potato": {"leaf_color": "dark green", "texture": "smooth compound leaves", "tip_condition": "no spots"},
    "maize": {"leaf_color": "deep green", "texture": "smooth, broad", "tip_condition": "no ragged edges"},
    "sugarcane": {"leaf_color": "bright green", "texture": "smooth, elongated", "tip_condition": "no drying"},
}


import random

async def detect_disease(
    image_path: str,
    crop_type: str | None,
    db: AsyncSession,
    user_id: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
) -> dict:
    """
    Analyze a crop image for disease detection.
    In production: runs ONNX model inference on the image.
    Current: uses knowledge base with simulated confidence.
    """

    # Default to rice if not specified
    crop = (crop_type or "rice").lower()
    if crop not in DISEASE_DATABASE:
        crop = "rice"

    diseases = DISEASE_DATABASE[crop]

    # Simulate detection (in production: model inference)
    # 30% chance healthy, 70% chance specific disease detected
    is_healthy = random.random() < 0.3

    if is_healthy:
        result = {
            "disease_name": "Healthy",
            "confidence": round(random.uniform(0.88, 0.98), 2),
            "severity": 0,
            "is_healthy": True,
            "treatment_chemical": "No treatment needed. Crop appears healthy.",
            "treatment_organic": "Continue current management practices. Regular scouting recommended weekly.",
            "prevention_tips": DISEASE_DATABASE[crop][0]["prevention"],
            "crop_type": crop,
        }
    else:
        disease = random.choice(diseases)
        severity = random.randint(disease["severity_range"][0], disease["severity_range"][1])
        result = {
            "disease_name": disease["name"],
            "confidence": round(random.uniform(0.72, 0.96), 2),
            "severity": severity,
            "is_healthy": False,
            "treatment_chemical": disease["chemical"],
            "treatment_organic": disease["organic"],
            "prevention_tips": disease["prevention"],
            "crop_type": crop,
        }

    # Save scan to database
    scan = CropScan(
        user_id=user_id,
        image_path=image_path,
        crop_type=crop,
        disease_name=result["disease_name"],
        confidence=result["confidence"],
        severity=result["severity"],
        is_healthy=result["is_healthy"],
        treatment_chemical=result["treatment_chemical"],
        treatment_organic=result["treatment_organic"],
        prevention_tips=result["prevention_tips"],
        latitude=lat,
        longitude=lon,
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    return {"id": str(scan.id), "result": result, "created_at": scan.created_at}


async def get_scan_history(db: AsyncSession, user_id: str, limit: int = 20) -> list[dict]:
    """Get recent scan history for a user."""
    stmt = (
        select(CropScan)
        .where(CropScan.user_id == user_id)
        .order_by(CropScan.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    scans = result.scalars().all()

    return [
        {
            "id": str(s.id),
            "crop_type": s.crop_type,
            "disease_name": s.disease_name,
            "confidence": s.confidence,
            "severity": s.severity,
            "is_healthy": s.is_healthy,
            "created_at": s.created_at,
        }
        for s in scans
    ]


def get_supported_crops() -> list[dict]:
    """Return list of supported crops with disease counts."""
    return [
        {"name": crop, "disease_count": len(diseases), "icon": _crop_icon(crop)}
        for crop, diseases in DISEASE_DATABASE.items()
    ]


def _crop_icon(crop: str) -> str:
    icons = {
        "rice": "🌾", "wheat": "🌾", "tomato": "🍅", "cotton": "🏵️",
        "potato": "🥔", "maize": "🌽", "sugarcane": "🎋",
    }
    return icons.get(crop, "🌱")
