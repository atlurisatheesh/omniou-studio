"""
AGRISENSE — Pydantic Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


# ── Auth ──

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    language: str = "en"
    region: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    language: str
    region: Optional[str] = None
    plan: str
    farm_size_acres: Optional[float] = None
    primary_crops: Optional[str] = None
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Disease Detection ──

class ScanRequest(BaseModel):
    crop_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class DiseaseResult(BaseModel):
    disease_name: str
    confidence: float
    severity: int  # 1-5
    is_healthy: bool
    treatment_chemical: str
    treatment_organic: str
    prevention_tips: str
    crop_type: str

class ScanResponse(BaseModel):
    id: str
    result: DiseaseResult
    created_at: datetime


# ── Soil Health ──

class SoilTestCreate(BaseModel):
    ph: Optional[float] = None
    nitrogen_kg_ha: Optional[float] = None
    phosphorus_kg_ha: Optional[float] = None
    potassium_kg_ha: Optional[float] = None
    organic_carbon_pct: Optional[float] = None
    ec_ds_m: Optional[float] = None
    zinc_ppm: Optional[float] = None
    iron_ppm: Optional[float] = None
    manganese_ppm: Optional[float] = None
    boron_ppm: Optional[float] = None
    sulphur_ppm: Optional[float] = None
    soil_type: Optional[str] = None
    target_crop: Optional[str] = None
    field_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class FertilizerRecommendation(BaseModel):
    nutrient: str
    current_value: Optional[float]
    optimal_range: str
    status: str  # deficient, optimal, excess
    recommendation: str
    quantity_per_acre: str

class SoilHealthResponse(BaseModel):
    id: str
    overall_health_score: float
    deficiencies: list[FertilizerRecommendation]
    recommendations: list[str]
    created_at: datetime


# ── Crop Calendar ──

class CropCalendarCreate(BaseModel):
    crop: str
    variety: Optional[str] = None
    sowing_date: str  # ISO date
    field_name: Optional[str] = None
    field_size_acres: Optional[float] = None
    region: Optional[str] = None

class CalendarActivity(BaseModel):
    day: int
    stage: str
    activity: str
    details: str
    type: str  # irrigation, fertilizer, spray, scout, harvest

class CropCalendarResponse(BaseModel):
    id: str
    crop: str
    variety: Optional[str]
    sowing_date: str
    expected_harvest_date: str
    current_stage: str
    activities: list[CalendarActivity]


# ── Weather ──

class WeatherCurrent(BaseModel):
    temp_c: float
    feels_like_c: float
    humidity_pct: float
    wind_speed_kmh: float
    description: str
    icon: str
    rain_mm: float = 0.0

class WeatherForecast(BaseModel):
    date: str
    temp_min_c: float
    temp_max_c: float
    humidity_pct: float
    rain_mm: float
    description: str
    icon: str
    spray_window: bool  # Safe to spray?
    spray_reason: str = ""

class WeatherResponse(BaseModel):
    location: str
    current: WeatherCurrent
    forecast: list[WeatherForecast]
    pest_risks: list[dict]


# ── Market Prices ──

class MarketPriceItem(BaseModel):
    commodity: str
    market_name: str
    state: str
    district: str
    min_price: float
    max_price: float
    modal_price: float
    arrival_date: str
    trend: str = "stable"  # up, down, stable
    trend_pct: float = 0.0

class MarketResponse(BaseModel):
    commodity: str
    prices: list[MarketPriceItem]
    avg_price: float
    best_market: str
    price_trend_7d: str


# ── Community ──

class PostCreate(BaseModel):
    title: str
    body: Optional[str] = None
    category: str = "general"
    crop: Optional[str] = None
    region: Optional[str] = None

class ReplyCreate(BaseModel):
    body: str

class PostResponse(BaseModel):
    id: str
    user_name: str
    title: str
    body: Optional[str]
    image_path: Optional[str]
    category: str
    crop: Optional[str]
    region: Optional[str]
    upvotes: int
    replies_count: int
    is_answered: bool
    created_at: datetime

class ReplyResponse(BaseModel):
    id: str
    user_name: str
    body: str
    is_expert: bool
    upvotes: int
    created_at: datetime
