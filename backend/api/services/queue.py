"""Simple Redis-backed task queue.

Enqueues jobs via LPUSH and workers consume via BRPOP.
Minimal dependency: only redis.asyncio.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from redis.asyncio import Redis

from api.config import get_settings

settings = get_settings()
QUEUE_KEY = "email_saas:queue"
DLQ_KEY = "email_saas:dlq"
MAX_RETRIES = 3


def _redis() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _encode_payload(
    job_type: str,
    job_id: str | uuid.UUID,
    account_id: str | uuid.UUID,
    payload: dict[str, Any],
    retry_count: int = 0,
) -> str:
    return json.dumps(
        {
            "job_type": job_type,
            "job_id": str(job_id),
            "account_id": str(account_id),
            "payload": payload,
            "retry_count": retry_count,
            "created_at": _now(),
        },
        default=str,
    )


def _decode_payload(raw: str) -> dict[str, Any]:
    return json.loads(raw)


async def enqueue(
    job_type: str,
    job_id: str | uuid.UUID,
    account_id: str | uuid.UUID,
    payload: dict[str, Any],
) -> None:
    """Push a job onto the queue."""
    redis = _redis()
    try:
        encoded = _encode_payload(job_type, job_id, account_id, payload)
        await redis.lpush(QUEUE_KEY, encoded)
    finally:
        await redis.close()


async def dequeue(timeout: float = 5.0) -> dict[str, Any] | None:
    """Blocking pop from the queue. Returns None on timeout."""
    redis = _redis()
    try:
        result = await redis.brpop(QUEUE_KEY, timeout=timeout)
        if result is None:
            return None
        _key, raw = result
        return _decode_payload(raw)
    finally:
        await redis.close()


async def requeue(job: dict[str, Any]) -> None:
    """Push a failed job back onto the queue with incremented retry_count,
    or move it to the dead-letter queue if retries exhausted.
    """
    redis = _redis()
    try:
        job["retry_count"] = job.get("retry_count", 0) + 1
        if job["retry_count"] >= MAX_RETRIES:
            job["failed_at"] = _now()
            await redis.lpush(DLQ_KEY, json.dumps(job, default=str))
        else:
            await redis.lpush(QUEUE_KEY, json.dumps(job, default=str))
    finally:
        await redis.close()


async def queue_length() -> int:
    """Return the number of pending jobs."""
    redis = _redis()
    try:
        return await redis.llen(QUEUE_KEY)
    finally:
        await redis.close()


async def dlq_length() -> int:
    """Return the number of dead-lettered jobs."""
    redis = _redis()
    try:
        return await redis.llen(DLQ_KEY)
    finally:
        await redis.close()
