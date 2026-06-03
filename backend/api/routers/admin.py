import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_settings
from api.db import get_db
from api.deps import (
    create_access_token,
    get_current_active_account,
    require_admin,
    require_superadmin,
    get_redis,
)
from api.models import (
    Account,
    AccountRole,
    AccountStatus,
    AuditLog,
    Domain,
    Mailbox,
    ProvisioningJob,
    Subscription,
    SubscriptionStatus,
    Ticket,
    TicketStatus,
    ActorType,
)
from api.schemas import (
    AdminAccountOut,
    AdminImpersonateOut,
    AdminImpersonateRequest,
    AdminStatsOut,
    AdminSuspendAccount,
    AuditLogOut,
    MessageOut,
    PaginatedResponse,
    ProvisioningJobOut,
    SubscriptionOut,
    TicketOut,
    UserOut,
)
from api.services.audit import audit_from_request
from api.services.metrics import get_mail_metrics

from redis.asyncio import Redis

router = APIRouter()
settings = get_settings()


@router.get("/metrics", response_model=dict)
async def get_metrics(
    db: AsyncSession = Depends(get_db),
    admin: Account = Depends(require_admin),
):
    return await get_mail_metrics(db)


@router.get("/accounts", response_model=PaginatedResponse[AdminAccountOut])
async def list_accounts(
    request: Request,
    page: int = 1,
    per_page: int = 20,
    status: AccountStatus | None = None,
    db: AsyncSession = Depends(get_db),
    admin: Account = Depends(require_admin),
):
    query = select(Account)
    count_query = select(func.count()).select_from(Account)
    if status:
        query = query.where(Account.status == status)
        count_query = count_query.where(Account.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(
        query.order_by(Account.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    )
    items = result.scalars().all()

    # Build enriched response
    out_items = []
    for acc in items:
        domain_count = await db.execute(
            select(func.count()).select_from(Domain).where(Domain.account_id == acc.id)
        )
        mailbox_count = await db.execute(
            select(func.count()).select_from(Mailbox).where(Mailbox.account_id == acc.id)
        )
        sub = await db.execute(
            select(Subscription).where(Subscription.account_id == acc.id)
        )
        sub_obj = sub.scalar_one_or_none()
        out_items.append(
            {
                "id": acc.id,
                "email": acc.email,
                "role": acc.role,
                "status": acc.status,
                "plan": acc.plan,
                "display_name": acc.display_name,
                "totp_enabled": acc.totp_enabled,
                "created_at": acc.created_at,
                "updated_at": acc.updated_at,
                "stripe_customer_id": acc.stripe_customer_id,
                "domain_count": domain_count.scalar() or 0,
                "mailbox_count": mailbox_count.scalar() or 0,
                "subscription_status": sub_obj.status.value if sub_obj else None,
            }
        )

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": out_items,
    }


@router.get("/accounts/{account_id}", response_model=AdminAccountOut)
async def get_account(
    request: Request,
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: Account = Depends(require_admin),
):
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    domain_count = await db.execute(
        select(func.count()).select_from(Domain).where(Domain.account_id == account.id)
    )
    mailbox_count = await db.execute(
        select(func.count()).select_from(Mailbox).where(Mailbox.account_id == account.id)
    )
    sub = await db.execute(
        select(Subscription).where(Subscription.account_id == account.id)
    )
    sub_obj = sub.scalar_one_or_none()
    return {
        "id": account.id,
        "email": account.email,
        "role": account.role,
        "status": account.status,
        "plan": account.plan,
        "display_name": account.display_name,
        "totp_enabled": account.totp_enabled,
        "created_at": account.created_at,
        "updated_at": account.updated_at,
        "stripe_customer_id": account.stripe_customer_id,
        "domain_count": domain_count.scalar() or 0,
        "mailbox_count": mailbox_count.scalar() or 0,
        "subscription_status": sub_obj.status.value if sub_obj else None,
    }


@router.post("/accounts/{account_id}/impersonate", response_model=AdminImpersonateOut)
async def impersonate(
    request: Request,
    account_id: uuid.UUID,
    data: AdminImpersonateRequest,
    db: AsyncSession = Depends(get_db),
    admin: Account = Depends(require_superadmin),
    redis: Redis = Depends(get_redis),
):
    if not data.reason or len(data.reason.strip()) < 5:
        raise HTTPException(status_code=400, detail="Impersonation reason required (min 5 characters)")
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    token = create_access_token(
        {
            "sub": str(account.id),
            "impersonated_by": str(admin.id),
            "impersonated_by_email": admin.email,
            "reason": data.reason,
        },
        expires_delta_minutes=settings.impersonate_token_expire_minutes,
        token_type="impersonate",
    )
    await redis.setex(
        f"session:{account.id}:impersonate",
        settings.impersonate_token_expire_minutes * 60,
        "active",
    )
    await audit_from_request(
        request,
        "impersonate",
        "account",
        str(account.id),
        account_id=account.id,
        actor_id=admin.id,
        actor_type=ActorType.impersonation,
        metadata={"impersonated_by": admin.email, "reason": data.reason, "ticket_id": data.ticket_id},
    )
    return {"token": token, "expires_in": settings.impersonate_token_expire_minutes * 60}


@router.post("/accounts/{account_id}/suspend", response_model=MessageOut)
async def suspend_account(
    request: Request,
    account_id: uuid.UUID,
    data: AdminSuspendAccount,
    db: AsyncSession = Depends(get_db),
    admin: Account = Depends(require_admin),
):
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    account.status = AccountStatus.suspended
    await db.commit()
    await audit_from_request(
        request,
        "suspend_account",
        "account",
        str(account.id),
        account_id=account.id,
        actor_id=admin.id,
        actor_type=ActorType.admin,
        metadata={"reason": data.reason},
    )
    return {"message": "Account suspended"}


@router.post("/accounts/{account_id}/unsuspend", response_model=MessageOut)
async def unsuspend_account(
    request: Request,
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: Account = Depends(require_admin),
):
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    account.status = AccountStatus.active
    await db.commit()
    await audit_from_request(
        request,
        "unsuspend_account",
        "account",
        str(account.id),
        account_id=account.id,
        actor_id=admin.id,
        actor_type=ActorType.admin,
    )
    return {"message": "Account unsuspended"}


@router.get("/jobs", response_model=PaginatedResponse[ProvisioningJobOut])
async def list_jobs(
    request: Request,
    page: int = 1,
    per_page: int = 20,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    admin: Account = Depends(require_admin),
):
    query = select(ProvisioningJob)
    count_query = select(func.count()).select_from(ProvisioningJob)
    if status:
        query = query.where(ProvisioningJob.status == status)
        count_query = count_query.where(ProvisioningJob.status == status)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    result = await db.execute(
        query.order_by(ProvisioningJob.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    )
    items = result.scalars().all()
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": items,
    }


@router.get("/stats", response_model=AdminStatsOut)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    admin: Account = Depends(require_admin),
):
    total_accounts = await db.execute(
        select(func.count()).select_from(Account)
    )
    active_accounts = await db.execute(
        select(func.count()).select_from(Account).where(Account.status == AccountStatus.active)
    )
    suspended_accounts = await db.execute(
        select(func.count()).select_from(Account).where(Account.status == AccountStatus.suspended)
    )
    total_domains = await db.execute(
        select(func.count()).select_from(Domain)
    )
    verified_domains = await db.execute(
        select(func.count()).select_from(Domain).where(Domain.verified == True)
    )
    total_mailboxes = await db.execute(
        select(func.count()).select_from(Mailbox)
    )
    open_tickets = await db.execute(
        select(func.count()).select_from(Ticket).where(Ticket.status == TicketStatus.open)
    )

    # MRR estimate: naive count of active subscriptions * price placeholder
    # Real implementation would use Stripe data
    mrr_estimate = 0
    subs = await db.execute(
        select(Subscription).where(Subscription.status == SubscriptionStatus.active)
    )
    for sub in subs.scalars().all():
        if sub.plan.value == "starter":
            mrr_estimate += 1000
        elif sub.plan.value == "pro":
            mrr_estimate += 2900
        elif sub.plan.value == "enterprise":
            mrr_estimate += 9900

    return {
        "total_accounts": total_accounts.scalar() or 0,
        "active_accounts": active_accounts.scalar() or 0,
        "suspended_accounts": suspended_accounts.scalar() or 0,
        "total_domains": total_domains.scalar() or 0,
        "verified_domains": verified_domains.scalar() or 0,
        "total_mailboxes": total_mailboxes.scalar() or 0,
        "open_tickets": open_tickets.scalar() or 0,
        "mrr_estimate_cents": mrr_estimate,
    }


@router.get("/audit-log", response_model=PaginatedResponse[AuditLogOut])
async def list_audit_log(
    page: int = 1,
    per_page: int = 50,
    db: AsyncSession = Depends(get_db),
    admin: Account = Depends(require_admin),
):
    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    count_query = select(func.count()).select_from(AuditLog)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    result = await db.execute(
        query.offset((page - 1) * per_page).limit(per_page)
    )
    items = result.scalars().all()
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": items,
    }
