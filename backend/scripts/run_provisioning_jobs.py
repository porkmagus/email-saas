#!/usr/bin/env python3
"""Provisioning job runner — retry pending and failed jobs.

Usage (inside backend container):
    python scripts/run_provisioning_jobs.py

Usage (from host):
    docker compose exec backend python scripts/run_provisioning_jobs.py

Intended to be called from a cron job or systemd timer.
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone

sys.path.insert(0, "/app")

from sqlalchemy import select, update
from api.db import async_session_maker
from api.models import ProvisioningJob, JobStatus
from api.services.provision import run_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def run_pending_jobs() -> int:
    """Run all pending / retryable jobs. Returns number of jobs processed."""
    processed = 0
    async with async_session_maker() as db:
        result = await db.execute(
            select(ProvisioningJob)
            .where(
                ProvisioningJob.status.in_([JobStatus.pending, JobStatus.failed])
            )
            .where(ProvisioningJob.retry_count < ProvisioningJob.max_retries)
            .order_by(ProvisioningJob.created_at)
        )
        jobs = result.scalars().all()

    for job in jobs:
        logger.info("Processing job %s (type=%s, status=%s, retry=%d/%d)",
                    job.id, job.type, job.status.value, job.retry_count, job.max_retries)

        # Increment retry count before running
        async with async_session_maker() as db:
            await db.execute(
                update(ProvisioningJob)
                .where(ProvisioningJob.id == job.id)
                .values(retry_count=ProvisioningJob.retry_count + 1)
            )
            await db.commit()

        try:
            await run_job(job.id)
            logger.info("Job %s completed successfully", job.id)
        except Exception as e:
            logger.error("Job %s failed: %s", job.id, e)

        processed += 1

    return processed


async def main():
    logger.info("Provisioning job runner starting...")
    processed = await run_pending_jobs()
    logger.info("Processed %d job(s)", processed)
    if processed == 0:
        logger.info("No jobs to process.")


if __name__ == "__main__":
    asyncio.run(main())
