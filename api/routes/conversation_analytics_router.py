"""
Conversation Analytics API Router
Provides endpoints for analytics, feedback, anomaly, and time series insights from conversation memory.
"""
from fastapi import APIRouter, Query
from typing import Optional
from services.conversation_memory import conversation_memory

router = APIRouter(prefix="/conversation-analytics", tags=["Conversation Analytics"])

@router.get("/memory-stats")
def get_memory_stats():
    """Get overall memory analytics summary."""
    return conversation_memory.get_memory_stats()

@router.get("/anomaly-report")
def get_anomaly_report():
    """Get all detected anomaly events."""
    return conversation_memory.get_anomaly_report()

@router.get("/feedback-summary")
def get_feedback_summary():
    """Get summary statistics for all feedback/evaluations."""
    return conversation_memory.get_feedback_summary()

@router.get("/common-feedback")
async def get_most_common_feedback(n: int = Query(3, ge=1, le=20)):
    """Get the n most common feedback strings (cached, async, productionized)."""
    redis = await get_redis_client()
    async def compute():
        async for session in db_service.get_async_session():
            return await conversation_memory.get_most_common_feedback(session, n=n)
    return await get_cached_or_compute(redis, f"most_common_feedback:{n}", compute)

@router.get("/message-volume-over-time")
async def get_message_volume_over_time(freq: str = Query('D', regex='^(D|H)$')):
    """Get message volume over time (by day or hour, cached, async, productionized)."""
    redis = await get_redis_client()
    async def compute():
        async for session in db_service.get_async_session():
            return await conversation_memory.get_message_volume_over_time(session, freq)
    return await get_cached_or_compute(redis, f"message_volume_over_time:{freq}", compute)

import json
from api.config.redis_config import get_redis_client, close_redis_connection
from api.services.database_service import DatabaseService
from fastapi import APIRouter

from sqlalchemy import text

db_service = DatabaseService()

@router.get("/health")
async def healthcheck():
    """Healthcheck for Redis and Postgres connectivity."""
    try:
        redis = await get_redis_client()
        await redis.ping()
        await close_redis_connection(redis)
        async for session in db_service.get_async_session():
            await session.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

async def get_cached_or_compute(redis, cache_key, compute_fn, expire=300):
    cached = await redis.get(cache_key)
    if cached:
        await close_redis_connection(redis)
        return json.loads(cached)
    result = await compute_fn()
    await redis.set(cache_key, json.dumps(result), ex=expire)
    await close_redis_connection(redis)
    return result

@router.get("/funnel-analysis")
async def get_funnel_analysis():
    """Get funnel analysis data (cached, async, productionized)."""
    redis = await get_redis_client()
    async def compute():
        async for session in db_service.get_async_session():
            # Replace with actual DB query logic as needed
            return await conversation_memory.get_funnel_analysis(session)
    return await get_cached_or_compute(redis, "funnel_analysis", compute)

@router.get("/user-segmentation")
def get_user_segmentation():
    """Get user segmentation data (e.g., by type, geography)."""
    return conversation_memory.get_user_segmentation()
