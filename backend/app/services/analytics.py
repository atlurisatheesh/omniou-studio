"""
services/analytics.py — Event tracking and aggregation service (Phase 12).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

log = structlog.get_logger(__name__)


class EventType(str, Enum):
    JOB_CREATED    = "job_created"
    JOB_COMPLETED  = "job_completed"
    JOB_FAILED     = "job_failed"
    JOB_CANCELLED  = "job_cancelled"
    STAGE_COMPLETE = "stage_complete"
    LOGIN          = "login"
    REGISTER       = "register"
    EXPORT         = "export"
    VOICE_CREATED  = "voice_created"
    TEMPLATE_USED  = "template_used"
    MULTI_FACE_JOB = "multi_face_job"


async def track_event(
    db: AsyncSession,
    event_type: EventType,
    user_id: Optional[str] = None,
    job_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    try:
        meta_json = json.dumps(metadata or {})
        await db.execute(
            text("""
                INSERT INTO analytics_events
                    (event_type, user_id, job_id, metadata, created_at)
                VALUES
                    (:event_type, :user_id, :job_id, :metadata, :created_at)
            """),
            {
                "event_type": event_type.value,
                "user_id": user_id,
                "job_id": job_id,
                "metadata": meta_json,
                "created_at": datetime.now(timezone.utc),
            },
        )
        await db.commit()
    except Exception as e:
        log.warning("analytics_event_failed", event=event_type, error=str(e))


async def get_daily_jobs(db: AsyncSession, days: int = 30) -> List[Dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    # Use SQLite-compatible query
    result = await db.execute(
        text("""
            SELECT
                DATE(created_at) AS day,
                SUM(CASE WHEN event_type = 'job_created' THEN 1 ELSE 0 END)   AS created,
                SUM(CASE WHEN event_type = 'job_completed' THEN 1 ELSE 0 END) AS completed,
                SUM(CASE WHEN event_type = 'job_failed' THEN 1 ELSE 0 END)    AS failed
            FROM analytics_events
            WHERE created_at >= :since
              AND event_type IN ('job_created', 'job_completed', 'job_failed')
            GROUP BY DATE(created_at)
            ORDER BY day ASC
        """),
        {"since": since},
    )
    return [dict(r._mapping) for r in result.fetchall()]


async def get_language_distribution(db: AsyncSession) -> List[Dict]:
    result = await db.execute(
        text("""
            SELECT
                JSON_EXTRACT(metadata, '$.language') AS language,
                COUNT(*) AS count
            FROM analytics_events
            WHERE event_type = 'job_created'
            GROUP BY JSON_EXTRACT(metadata, '$.language')
            ORDER BY count DESC
            LIMIT 20
        """)
    )
    return [dict(r._mapping) for r in result.fetchall()]


async def get_engine_usage(db: AsyncSession) -> List[Dict]:
    result = await db.execute(
        text("""
            SELECT
                JSON_EXTRACT(metadata, '$.engine') AS engine,
                COUNT(*) AS count
            FROM analytics_events
            WHERE event_type = 'stage_complete'
            GROUP BY JSON_EXTRACT(metadata, '$.engine')
            ORDER BY count DESC
        """)
    )
    return [dict(r._mapping) for r in result.fetchall() if r[0]]


async def get_processing_time_trend(db: AsyncSession, days: int = 14) -> List[Dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        text("""
            SELECT
                DATE(created_at) AS day,
                AVG(CAST(JSON_EXTRACT(metadata,'$.processing_time_sec') AS REAL)) AS avg_sec,
                MIN(CAST(JSON_EXTRACT(metadata,'$.processing_time_sec') AS REAL)) AS min_sec,
                MAX(CAST(JSON_EXTRACT(metadata,'$.processing_time_sec') AS REAL)) AS max_sec
            FROM analytics_events
            WHERE event_type = 'job_completed' AND created_at >= :since
            GROUP BY DATE(created_at)
            ORDER BY day ASC
        """),
        {"since": since},
    )
    return [dict(r._mapping) for r in result.fetchall()]


async def get_quality_score_distribution(db: AsyncSession) -> Dict:
    result = await db.execute(
        text("""
            SELECT
                AVG(CAST(JSON_EXTRACT(metadata, '$.quality_score') AS REAL))  AS avg_quality,
                AVG(CAST(JSON_EXTRACT(metadata, '$.sync_score') AS REAL))    AS avg_sync,
                AVG(CAST(JSON_EXTRACT(metadata, '$.ai_detect_pct') AS REAL)) AS avg_ai_detect,
                COUNT(*) AS total
            FROM analytics_events
            WHERE event_type = 'job_completed'
        """)
    )
    row = result.fetchone()
    if row:
        return dict(row._mapping)
    return {}


async def get_platform_summary(db: AsyncSession) -> Dict:
    result = await db.execute(
        text("""
            SELECT
                SUM(CASE WHEN event_type = 'job_created' THEN 1 ELSE 0 END)   AS total_jobs,
                SUM(CASE WHEN event_type = 'job_completed' THEN 1 ELSE 0 END) AS completed_jobs,
                SUM(CASE WHEN event_type = 'job_failed' THEN 1 ELSE 0 END)    AS failed_jobs,
                SUM(CASE WHEN event_type = 'register' THEN 1 ELSE 0 END)      AS total_signups,
                COUNT(DISTINCT user_id)                                         AS active_users
            FROM analytics_events
            WHERE created_at >= :since
        """),
        {"since": datetime.now(timezone.utc) - timedelta(days=30)},
    )
    row = result.fetchone()
    if row:
        d = dict(row._mapping)
        total = d.get("total_jobs") or 1
        d["success_rate"] = round((d.get("completed_jobs") or 0) / total * 100, 1)
        return d
    return {}
