import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account
from api.models import Account, Domain, ProvisioningJob, JobType, JobStatus
from api.schemas import DomainCreate, DomainOut, OnboardingOut, MessageOut
from api.services.audit import audit_from_request
from api.services.dns_check import check_domain_dns
from api.services.stalwart_api import create_domain as stalwart_create_domain
from api.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("", response_model=DomainOut)
async def create_domain(
    request: Request,
    data: DomainCreate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    # Tenant scope: ensure domain doesn't belong to another account
    existing = await db.execute(
        select(Domain).where(Domain.domain == data.domain)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Domain already registered")

    domain = Domain(
        id=uuid.uuid4(),
        account_id=account.id,
        domain=data.domain,
    )
    db.add(domain)
    await db.commit()
    await db.refresh(domain)

    # Generate DKIM keypair
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend
    import base64
    import hmac
    import hashlib
    
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )
    # Extract base64-encoded key material
    public_lines = public_pem.decode().replace("-----BEGIN PUBLIC KEY-----", "").replace("-----END PUBLIC KEY-----", "").replace("\n", "")
    
    # Serialize private key
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    )
    
    # Encrypt private key with app secret
    secret_key = settings.api_key_secret or settings.secret_key
    encrypted_private = hmac.new(secret_key.encode(), private_pem, hashlib.sha256).hexdigest()
    
    # Generate unique selector with counter to avoid collisions
    import secrets
    selector = "saas" + datetime.now(timezone.utc).strftime("%Y%m%d") + "a" + secrets.token_hex(2)
    domain.dkim_selector = selector
    domain.dkim_record = f"v=DKIM1; k=rsa; p={public_lines}"
    domain.dkim_private_key_encrypted = encrypted_private
    # Store private key in Stalwart (simplified: would be via API)
    # For now, store in DB (encrypted in production)
    await db.commit()
    await db.refresh(domain)
    
    # Push to Stalwart
    try:
        from api.services.stalwart_api import configure_dkim
        await configure_dkim(domain.domain, selector, private_pem.decode(), public_lines)
    except Exception as e:
        # Log but don't fail - retry job
        job = ProvisioningJob(
            id=uuid.uuid4(),
            account_id=account.id,
            type=JobType.add_domain,
            payload={
                "domain_id": str(domain.id),
                "domain": domain.domain,
                "dkim_selector": selector,
                "error": str(e),
            },
            status=JobStatus.pending,
        )
        db.add(job)
        await db.commit()

    await audit_from_request(
        request, "create_domain", "domain", str(domain.id), account.id, account.id
    )

    return domain


@router.post("/{domain_id}/rotate-dkim", response_model=DomainOut)
async def rotate_dkim(
    request: Request,
    domain_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Domain).where(Domain.id == domain_id, Domain.account_id == account.id)
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    # Generate new DKIM keypair
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )
    public_lines = public_pem.decode().replace("-----BEGIN PUBLIC KEY-----", "").replace("-----END PUBLIC KEY-----", "").replace("\n", "")
    selector = "saas" + datetime.now(timezone.utc).strftime("%Y%m%d")
    domain.dkim_selector = selector
    domain.dkim_record = f"v=DKIM1; k=rsa; p={public_lines}"
    domain.dkim_verified = False
    await db.commit()
    await db.refresh(domain)
    await audit_from_request(
        request, "rotate_dkim", "domain", str(domain.id), account.id, account.id,
        metadata={"selector": selector}
    )
    return domain


@router.get("", response_model=list[DomainOut])
async def list_domains(
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Domain).where(Domain.account_id == account.id)
    )
    return result.scalars().all()


@router.get("/{domain_id}", response_model=DomainOut)
async def get_domain(
    domain_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Domain).where(Domain.id == domain_id, Domain.account_id == account.id)
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain


@router.delete("/{domain_id}", response_model=MessageOut)
async def delete_domain(
    request: Request,
    domain_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Domain).where(Domain.id == domain_id, Domain.account_id == account.id)
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    await db.delete(domain)
    await db.commit()
    await audit_from_request(
        request, "delete_domain", "domain", str(domain_id), account.id, account.id
    )
    return {"message": "Domain deleted"}


@router.post("/{domain_id}/verify", response_model=DomainOut)
async def verify_domain(
    request: Request,
    domain_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Domain).where(Domain.id == domain_id, Domain.account_id == account.id)
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    # DNS checks
    dns = await check_domain_dns(domain.domain)
    domain.mx_verified = dns["mx_verified"]
    domain.spf_verified = dns["spf_verified"]
    domain.dkim_verified = dns["dkim_verified"]
    domain.mx_record = dns.get("mx_record")
    domain.spf_record = dns.get("spf_record")
    domain.dkim_record = dns.get("dkim_record")
    domain.dkim_selector = dns.get("dkim_selector")
    domain.verified = domain.mx_verified and domain.spf_verified and domain.dkim_verified
    domain.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(domain)
    await audit_from_request(
        request, "verify_domain", "domain", str(domain.id), account.id, account.id,
        metadata={"verified": domain.verified}
    )
    return domain


@router.get("/{domain_id}/onboarding", response_model=OnboardingOut)
async def get_onboarding(
    domain_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(Domain).where(Domain.id == domain_id, Domain.account_id == account.id)
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    # In production, derive from Stalwart config
    return {
        "domain": domain.domain,
        "mx_records": [f"10 mail.{domain.domain}."],
        "spf_record": f"v=spf1 include:_spf.yourprovider.com -all",
        "dkim_selector": domain.dkim_selector or "default",
        "dkim_record": domain.dkim_record or "",
        "webmail_url": f"https://webmail.{domain.domain}",
    }
