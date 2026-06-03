import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import async_session_maker
from api.models import ProvisioningJob, JobStatus, Account, Domain, Mailbox
from api.services.stalwart_api import create_domain, create_mailbox, delete_mailbox as stalwart_delete_mailbox


async def run_job(job_id: uuid.UUID) -> None:
    async with async_session_maker() as db:
        result = await db.execute(
            select(ProvisioningJob).where(ProvisioningJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            return

        await db.execute(
            update(ProvisioningJob)
            .where(ProvisioningJob.id == job_id)
            .values(status=JobStatus.running)
        )
        await db.commit()

        try:
            if job.type == "provision_account":
                # placeholder: could create default resources in Stalwart
                pass
            elif job.type == "add_domain":
                payload = job.payload
                await create_domain(payload["domain"])
            elif job.type == "add_mailbox":
                # NOTE: Mailbox creation is now synchronous in the API.
                # This handler only processes retry jobs.
                # The payload contains domain_id and local_part; the worker
                # looks up the domain and mailbox from the DB.
                # For the password, the worker needs a secure password store
                # integration (not yet implemented).
                payload = job.payload
                domain_id = payload.get("domain_id")
                local_part = payload.get("local_part")
                if domain_id and local_part:
                    domain_result = await db.execute(
                        select(Domain).where(Domain.id == uuid.UUID(domain_id))
                    )
                    domain = domain_result.scalar_one_or_none()
                    if domain:
                        # Without the plaintext password, we can't create the mailbox.
                        # This is a known limitation pending secure password storage.
                        raise RuntimeError(
                            "Mailbox retry requires plaintext password. "
                            "Secure password storage integration is pending."
                        )
                else:
                    raise ValueError("Missing domain_id or local_part in job payload")
            elif job.type == "delete_mailbox":
                # NOTE: Mailbox deletion is now synchronous in the API.
                # This handler only processes retry jobs.
                payload = job.payload
                domain_id = payload.get("domain_id")
                local_part = payload.get("local_part")
                if domain_id and local_part:
                    domain_result = await db.execute(
                        select(Domain).where(Domain.id == uuid.UUID(domain_id))
                    )
                    domain = domain_result.scalar_one_or_none()
                    if domain:
                        await stalwart_delete_mailbox(f"{local_part}@{domain.domain}")
                else:
                    raise ValueError("Missing domain_id or local_part in job payload")
            elif job.type == "suspend_account":
                # placeholder: suspend in Stalwart
                pass
            elif job.type == "delete_account":
                # placeholder: cleanup in Stalwart
                pass
            else:
                raise ValueError(f"Unknown job type {job.type}")

            await db.execute(
                update(ProvisioningJob)
                .where(ProvisioningJob.id == job_id)
                .values(
                    status=JobStatus.completed,
                    completed_at=datetime.now(timezone.utc),
                )
            )
            await db.commit()
        except Exception as e:
            await db.execute(
                update(ProvisioningJob)
                .where(ProvisioningJob.id == job_id)
                .values(
                    status=JobStatus.failed,
                    error=str(e),
                    completed_at=datetime.now(timezone.utc),
                )
            )
            await db.commit()
