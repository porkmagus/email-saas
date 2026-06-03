import uuid
from datetime import datetime
from typing import Literal, TypeVar, Generic

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from api.models import (
    AccountRole,
    AccountStatus,
    ActorType,
    JobStatus,
    JobType,
    MeteringEventType,
    PlanTier,
    SubscriptionStatus,
    TicketCategory,
    TicketPriority,
    TicketStatus,
)

# ---------------------------------------------------------------------------
# Base schemas
# ---------------------------------------------------------------------------

class UserBase(BaseModel):
    email: EmailStr
    display_name: str | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: AccountRole
    status: AccountStatus
    plan: PlanTier
    totp_enabled: bool
    created_at: datetime
    updated_at: datetime


class UserProfileUpdate(BaseModel):
    display_name: str | None = None


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)


# ---------------------------------------------------------------------------
# Auth response
# ---------------------------------------------------------------------------

class AuthOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    account: UserOut


# ---------------------------------------------------------------------------
# 2FA
# ---------------------------------------------------------------------------

class TOTPSetup(BaseModel):
    secret: str
    uri: str


class TOTPVerify(BaseModel):
    code: str = Field(min_length=6, max_length=6)


class TOTPRecoveryRequest(BaseModel):
    email: EmailStr
    password: str
    recovery_code: str = Field(min_length=16, max_length=20)


class TOTPDisable(BaseModel):
    code: str = Field(min_length=6, max_length=6)


# ---------------------------------------------------------------------------
# API Keys
# ---------------------------------------------------------------------------

class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    permissions: list[str] = Field(default_factory=lambda: ["smtp", "imap", "api_read"])


class ApiKeyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    name: str
    prefix: str
    permissions: list[str]
    last_used_at: datetime | None
    created_at: datetime
    revoked_at: datetime | None


class ApiKeyWithSecret(ApiKeyOut):
    secret: str


class ApiKeyRevoke(BaseModel):
    id: uuid.UUID


# ---------------------------------------------------------------------------
# Domain schemas
# ---------------------------------------------------------------------------

class DomainBase(BaseModel):
    domain: str = Field(min_length=1, max_length=255)


class DomainCreate(DomainBase):
    pass


class DomainVerify(BaseModel):
    id: uuid.UUID


class DomainOut(DomainBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    verified: bool
    mx_verified: bool
    spf_verified: bool
    dkim_verified: bool
    dkim_selector: str | None
    mx_record: str | None
    spf_record: str | None
    dkim_record: str | None
    created_at: datetime
    updated_at: datetime


class OnboardingOut(BaseModel):
    domain: str
    mx_records: list[str]
    spf_record: str
    dkim_selector: str
    dkim_record: str
    webmail_url: str


class DNSGuideRecord(BaseModel):
    name: str
    type: str
    value: str
    priority: int | None = None
    ttl: int = 3600
    instructions: str


class DNSGuideStep(BaseModel):
    step: int
    title: str
    description: str
    records: list[DNSGuideRecord]
    tips: list[str]


class DNSGuideProvider(BaseModel):
    name: str
    slug: str
    dns_url: str
    instructions: list[str]


class DNSGuideOut(BaseModel):
    domain: str
    providers: list[DNSGuideProvider]
    steps: list[DNSGuideStep]
    troubleshooting: list[str]
    propagation_note: str
    mx_server: str
    webmail_url: str
    dmarc_record: str


# ---------------------------------------------------------------------------
# Mailbox schemas
# ---------------------------------------------------------------------------

class MailboxBase(BaseModel):
    local_part: str = Field(min_length=1, max_length=255)
    display_name: str | None = None
    quota_bytes: int = Field(default=1073741824, ge=0)


class MailboxCreate(MailboxBase):
    domain_id: uuid.UUID
    password: str = Field(min_length=8)


class MailboxUpdate(BaseModel):
    display_name: str | None = None
    quota_bytes: int | None = Field(default=None, ge=0)
    password: str | None = Field(default=None, min_length=8)


class MailboxOut(MailboxBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    domain_id: uuid.UUID
    domain: str | None = None
    status: AccountStatus
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Subscription schemas
# ---------------------------------------------------------------------------

class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    stripe_subscription_id: str
    status: SubscriptionStatus
    current_period_end: datetime | None
    cancel_at_period_end: bool
    plan: PlanTier
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Provisioning job schemas
# ---------------------------------------------------------------------------

class ProvisioningJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    type: JobType
    payload: dict
    status: JobStatus
    error: str | None
    created_at: datetime
    completed_at: datetime | None


# ---------------------------------------------------------------------------
# Ticket schemas
# ---------------------------------------------------------------------------

class TicketCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1)
    category: TicketCategory = TicketCategory.other


class TicketCommentCreate(BaseModel):
    body: str = Field(min_length=1)
    is_internal: bool = False


class TicketCommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ticket_id: uuid.UUID
    author_id: uuid.UUID | None
    author_email: str | None
    is_internal: bool
    body: str
    created_at: datetime


class TicketUpdate(BaseModel):
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    assigned_to: str | None = None


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    title: str
    status: TicketStatus
    priority: TicketPriority
    category: TicketCategory
    assigned_to: str | None
    created_at: datetime
    updated_at: datetime
    comments: list[TicketCommentOut] = []


# ---------------------------------------------------------------------------
# Audit log schemas
# ---------------------------------------------------------------------------

class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID | None
    actor_id: uuid.UUID | None
    actor_type: ActorType
    action: str
    resource_type: str
    resource_id: str | None
    meta_data: dict | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime


# ---------------------------------------------------------------------------
# Suppression schemas
# ---------------------------------------------------------------------------

class SuppressionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    domain: str | None
    reason: str
    source: str | None
    created_at: datetime


# ---------------------------------------------------------------------------
# Metering schemas
# ---------------------------------------------------------------------------

class MeteringEventIn(BaseModel):
    event_type: MeteringEventType
    quantity: int = Field(ge=0)


class MeteringEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    event_type: MeteringEventType
    quantity: int
    period_start: datetime
    period_end: datetime
    created_at: datetime


# ---------------------------------------------------------------------------
# Admin schemas
# ---------------------------------------------------------------------------

class AdminAccountOut(UserOut):
    stripe_customer_id: str | None
    domain_count: int
    mailbox_count: int
    subscription_status: str | None


class AdminSuspendAccount(BaseModel):
    reason: str = Field(min_length=1)


class AdminImpersonateOut(BaseModel):
    token: str
    expires_in: int


class AdminImpersonateRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=500)
    ticket_id: str | None = None


class AdminStatsOut(BaseModel):
    total_accounts: int
    active_accounts: int
    suspended_accounts: int
    total_domains: int
    verified_domains: int
    total_mailboxes: int
    open_tickets: int
    mrr_estimate_cents: int


# ---------------------------------------------------------------------------
# Stripe
# ---------------------------------------------------------------------------

class StripeCheckoutOut(BaseModel):
    url: str


class StripePortalOut(BaseModel):
    url: str


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthOut(BaseModel):
    status: Literal["ok", "degraded", "error"]
    database: Literal["ok", "error"]
    redis: Literal["ok", "error"]


# ---------------------------------------------------------------------------
# Generic
# ---------------------------------------------------------------------------

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    page: int
    per_page: int
    items: list[T]


class MessageOut(BaseModel):
    message: str


class ErrorOut(BaseModel):
    detail: str
