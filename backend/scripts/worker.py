"""Redis queue worker for background import/export jobs.

Run with:
    python -m scripts.worker
Or in production:
    python -m scripts.worker --poll-interval 1.0
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import async_session_maker
from api.models import ExportJob, ImportJob
from api.services.queue import dequeue, requeue

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("worker")


async def _process_import_job(db: AsyncSession, payload: dict) -> None:
    """Placeholder import processing: connect to IMAP, fetch messages, save.
    For now, just mark as completed.
    """
    job_id = uuid.UUID(payload["job_id"])
    result = await db.execute(select(ImportJob).where(ImportJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        logger.warning("Import job %s not found", job_id)
        return
    job.status = "running"
    job.started_at = datetime.now(timezone.utc)
    await db.commit()
    # Placeholder: real work here
    job.status = "completed"
    job.completed_at = datetime.now(timezone.utc)
    job.messages_imported = 0
    await db.commit()
    logger.info("Import job %s completed", job_id)


async def _process_export_job(db: AsyncSession, payload: dict) -> None:
    """Placeholder export processing: generate file and store metadata.
    For now, just mark as completed.
    """
    job_id = uuid.UUID(payload["job_id"])
    result = await db.execute(select(ExportJob).where(ExportJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        logger.warning("Export job %s not found", job_id)
        return
    job.status = "running"
    job.started_at = datetime.now(timezone.utc)
    await db.commit()
    # Placeholder: real work here
    job.status = "completed"
    job.completed_at = datetime.now(timezone.utc)
    job.file_path = f"/tmp/export_{job.id}_{job.type}.tmp"
    job.file_size = 0
    await db.commit()
    logger.info("Export job %s completed", job_id)


async def _handle_job(job: dict) -> bool:
    """Process a single job. Return True on success, False on failure."""
    job_type = job.get("job_type")
    async with async_session_maker() as db:
        try:
            if job_type == "import":
                await _process_import_job(db, job)
            elif job_type == "export":
                await _process_export_job(db, job)
            else:
                logger.warning("Unknown job type: %s", job_type)
            return True
        except Exception as exc:
            logger.exception("Job %s failed: %s", job.get("job_id"), exc)
            await db.rollback()
            return False


async def run_worker(poll_interval: float = 5.0) -> None:
    """Main worker loop."""
    logger.info("Worker started (poll_interval=%.1fs)", poll_interval)
    while True:
        job = await dequeue(timeout=poll_interval)
        if job is None:
            continue
        success = await _handle_job(job)
        if not success:
            await requeue(job)


def main() -> None:
    parser = argparse.ArgumentParser(description="Email SaaS background worker")
    parser.add_argument("--poll-interval", type=float, default=5.0, help="Seconds to wait between polls")
    args = parser.parse_args()
    try:
        asyncio.run(run_worker(poll_interval=args.poll_interval))
    except KeyboardInterrupt:
        logger.info("Worker stopped")


if __name__ == "__main__":
    main()
