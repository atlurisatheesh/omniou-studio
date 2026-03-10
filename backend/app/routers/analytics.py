"""
routers/analytics.py — Analytics endpoints (Phase 12).

GET /analytics/summary         → 30-day platform overview
GET /analytics/daily-jobs      → jobs per day time series
GET /analytics/languages       → language usage breakdown
GET /analytics/engines         → AI engine usage
GET /analytics/processing-time → average processing time trend
GET /analytics/quality-scores  → quality metrics distribution
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.services.analytics import (
    get_daily_jobs,
    get_engine_usage,
    get_language_distribution,
    get_platform_summary,
    get_processing_time_trend,
    get_quality_score_distribution,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def analytics_summary(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    return await get_platform_summary(db)


@router.get("/daily-jobs")
async def analytics_daily_jobs(
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
) -> List[Dict]:
    return await get_daily_jobs(db, days)


@router.get("/languages")
async def analytics_languages(db: AsyncSession = Depends(get_db)) -> List[Dict]:
    return await get_language_distribution(db)


@router.get("/engines")
async def analytics_engines(db: AsyncSession = Depends(get_db)) -> List[Dict]:
    return await get_engine_usage(db)


@router.get("/processing-time")
async def analytics_processing_time(
    days: int = Query(14, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
) -> List[Dict]:
    return await get_processing_time_trend(db, days)


@router.get("/quality-scores")
async def analytics_quality(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    return await get_quality_score_distribution(db)
