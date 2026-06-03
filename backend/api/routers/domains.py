import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account
from api.models import Account, Domain, ProvisioningJob, JobType, JobStatus
from api.schemas import DomainCreate, DomainOut, OnboardingOut, DNSGuideOut, MessageOut
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


@router.get("/{domain_id}/dns-guide", response_model=DNSGuideOut)
async def get_dns_guide(
    domain_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    """Get a step-by-step DNS setup guide for a domain."""
    result = await db.execute(
        select(Domain).where(Domain.id == domain_id, Domain.account_id == account.id)
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    dkim_selector = domain.dkim_selector or "default"
    dkim_record = domain.dkim_record or ""
    mx_server = f"mail.{domain.domain}"
    webmail_url = f"https://webmail.{domain.domain}"
    dmarc_record = f"v=DMARC1; p=quarantine; rua=mailto:dmarc@{domain.domain}"

    providers = [
        {
            "name": "Cloudflare",
            "slug": "cloudflare",
            "dns_url": f"https://dash.cloudflare.com/",
            "instructions": [
                "Log in to your Cloudflare dashboard",
                "Select your domain",
                "Click 'DNS' in the left sidebar",
                "Click 'Add record' for each record below",
            ],
        },
        {
            "name": "GoDaddy",
            "slug": "godaddy",
            "dns_url": f"https://dcc.godaddy.com/manage/{domain.domain}/dns",
            "instructions": [
                "Log in to your GoDaddy account",
                "Go to 'My Products' → 'Domains'",
                "Click 'DNS' next to your domain",
                "Click 'Add' under each record type",
            ],
        },
        {
            "name": "Namecheap",
            "slug": "namecheap",
            "dns_url": f"https://ap.www.namecheap.com/domain/domaincontrolpanel/{domain.domain}/domain",
            "instructions": [
                "Log in to your Namecheap account",
                "Go to 'Domain List' → 'Manage' for your domain",
                "Click 'Advanced DNS' tab",
                "Click 'Add New Record' for each record",
            ],
        },
        {
            "name": "Google Domains",
            "slug": "google",
            "dns_url": f"https://domains.google.com/registrar/{domain.domain}/dns",
            "instructions": [
                "Log in to Google Domains",
                "Click your domain → 'DNS' tab",
                "Click 'Manage custom records'",
                "Click 'Create new record' for each entry",
            ],
        },
        {
            "name": "Other / Custom",
            "slug": "other",
            "dns_url": "",
            "instructions": [
                "Log in to your domain registrar or DNS provider",
                "Find the 'DNS Management' or 'Nameservers' section",
                "Look for 'Add Record' or 'Custom Records'",
                "Add the records shown below exactly as shown",
            ],
        },
    ]

    steps = [
        {
            "step": 1,
            "title": "Add MX Record (to receive email)",
            "description": "This tells the internet where to deliver mail for your domain. Without this, nobody can send you email.",
            "records": [
                {
                    "name": "@",
                    "type": "MX",
                    "value": mx_server,
                    "priority": 10,
                    "ttl": 3600,
                    "instructions": "Add an MX record with host '@' (or your domain name), pointing to the mail server above. Priority should be 10.",
                },
            ],
            "tips": [
                "Some providers use '@' for the root domain, others require you to type the full domain name.",
                "If you already have an MX record, you may need to remove it first (only one MX record should be active).",
                "Priority 10 means 'try this server first'. Lower numbers = higher priority.",
            ],
        },
        {
            "step": 2,
            "title": "Add SPF Record (to prevent spoofing)",
            "description": "SPF tells email providers which servers are allowed to send mail for your domain. Without this, your emails may be marked as spam.",
            "records": [
                {
                    "name": "@",
                    "type": "TXT",
                    "value": f"v=spf1 include:_spf.yourprovider.com -all",
                    "ttl": 3600,
                    "instructions": "Add a TXT record with host '@' and the value shown above. This is a single text string.",
                },
            ],
            "tips": [
                "You can only have ONE SPF record per domain. If you already have one, merge it with this value.",
                "Example merge: v=spf1 include:_spf.yourprovider.com include:_spf.google.com -all",
                "The '-all' at the end means 'reject all mail from servers not listed here'.",
            ],
        },
        {
            "step": 3,
            "title": "Add DKIM Record (to prove authenticity)",
            "description": "DKIM adds a digital signature to every email you send. Recipients use this to verify the email really came from you.",
            "records": [
                {
                    "name": f"{dkim_selector}._domainkey",
                    "type": "TXT",
                    "value": dkim_record,
                    "ttl": 3600,
                    "instructions": f"Add a TXT record with host '{dkim_selector}._domainkey' and the DKIM value shown above. This is a long text string.",
                },
            ],
            "tips": [
                "The host name is critical: it must be exactly '{dkim_selector}._domainkey' (do not include your domain).",
                "Some providers split long TXT values into multiple quoted strings. This is fine — they will be combined automatically.",
                "If the DKIM value is truncated, click 'Copy' and paste it directly to avoid errors.",
            ],
        },
        {
            "step": 4,
            "title": "Add DMARC Record (recommended for deliverability)",
            "description": "DMARC tells receiving servers what to do if SPF or DKIM checks fail. It also sends you reports about email delivery.",
            "records": [
                {
                    "name": "_dmarc",
                    "type": "TXT",
                    "value": dmarc_record,
                    "ttl": 3600,
                    "instructions": "Add a TXT record with host '_dmarc' and the value shown above.",
                },
            ],
            "tips": [
                "p=quarantine means 'suspicious emails go to spam'. After 30 days, change to p=reject for stronger protection.",
                "rua=mailto:dmarc@yourdomain.com sends aggregate reports to that address. Create that mailbox first.",
                "DMARC is optional but strongly recommended for business email.",
            ],
        },
    ]

    troubleshooting = [
        "Wait 5-30 minutes after adding DNS records before clicking Verify. Some providers are slower.",
        "If verification fails, check for extra spaces at the beginning or end of the record value.",
        "Make sure you are adding the record to the correct domain (not a subdomain unless intended).",
        "If you already have an SPF record, merge it rather than adding a second one. Multiple SPF records break email.",
        "Some providers use 'Name' instead of 'Host' — they mean the same thing.",
        "If DKIM is too long, your provider may split it into multiple quoted parts. This is normal and works.",
        "Use the provider's own DNS lookup tool first, then try our Verify button.",
    ]

    return {
        "domain": domain.domain,
        "providers": providers,
        "steps": steps,
        "troubleshooting": troubleshooting,
        "propagation_note": "DNS changes typically take 5-30 minutes to propagate globally, but can take up to 24 hours in rare cases.",
        "mx_server": mx_server,
        "webmail_url": webmail_url,
        "dmarc_record": dmarc_record,
    }

