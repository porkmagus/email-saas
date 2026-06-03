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
    sieve_script: str | None
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
    catch_all_target_mailbox_id: uuid.UUID | None
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


# ---------------------------------------------------------------------------
# Outbox schemas
# ---------------------------------------------------------------------------

class OutboxMessageCreate(BaseModel):
    from_address: str
    to_addresses: list[str]
    subject: str
    text_body: str | None = None
    html_body: str | None = None
    scheduled_at: datetime | None = None


class OutboxMessageUpdate(BaseModel):
    subject: str | None = None
    to_addresses: list[str] | None = None
    text_body: str | None = None
    html_body: str | None = None
    scheduled_at: datetime | None = None


class OutboxMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    from_address: str
    to_addresses: list[str]
    subject: str
    text_body: str | None = None
    html_body: str | None = None
    scheduled_at: datetime | None = None
    status: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Alias schemas
# ---------------------------------------------------------------------------

class AliasCreate(BaseModel):
    domain_id: uuid.UUID
    local_part: str = Field(min_length=1, max_length=255)
    target_mailbox_id: uuid.UUID


class AliasUpdate(BaseModel):
    is_active: bool | None = None
    target_mailbox_id: uuid.UUID | None = None


class AliasOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    domain_id: uuid.UUID
    local_part: str
    target_mailbox_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Blocked sender schemas
# ---------------------------------------------------------------------------

class BlockedSenderCreate(BaseModel):
    email_or_domain: str = Field(min_length=1, max_length=255)


class BlockedSenderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    email_or_domain: str
    is_domain: bool
    created_at: datetime


# ---------------------------------------------------------------------------
# Email rule schemas
# ---------------------------------------------------------------------------

class EmailRuleConditionCreate(BaseModel):
    field: str = Field(min_length=1)
    operator: str = Field(min_length=1)
    value: str = Field(min_length=1, max_length=500)


class EmailRuleConditionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    field: str
    operator: str
    value: str
    created_at: datetime


class EmailRuleActionCreate(BaseModel):
    action_type: str = Field(min_length=1)
    target_mailbox_id: uuid.UUID | None = None
    label: str | None = None


class EmailRuleActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    action_type: str
    target_mailbox_id: uuid.UUID | None
    label: str | None
    created_at: datetime


class EmailRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    priority: int = 0
    conditions: list[EmailRuleConditionCreate]
    actions: list[EmailRuleActionCreate]


class EmailRuleUpdate(BaseModel):
    name: str | None = None
    priority: int | None = None
    is_active: bool | None = None
    conditions: list[EmailRuleConditionCreate] | None = None
    actions: list[EmailRuleActionCreate] | None = None


class EmailRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    name: str
    priority: int
    is_active: bool
    custom_sieve: str | None
    conditions: list[EmailRuleConditionOut] = []
    actions: list[EmailRuleActionOut] = []
    created_at: datetime
    updated_at: datetime


class CustomSieveUpdate(BaseModel):
    custom_sieve: str | None = None


class SieveUpdate(BaseModel):
    script: str = Field(min_length=1)


class SieveValidate(BaseModel):
    script: str = Field(min_length=1)


class SieveValidateOut(BaseModel):
    valid: bool
    errors: list[str]


# ---------------------------------------------------------------------------
# Vacation response schemas
# ---------------------------------------------------------------------------

class VacationResponseCreate(BaseModel):
    is_active: bool
    subject: str | None = Field(default=None, max_length=500)
    body: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    only_contacts: bool = False
    only_aliases: bool = False


class VacationResponseUpdate(BaseModel):
    is_active: bool | None = None
    subject: str | None = Field(default=None, max_length=500)
    body: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    only_contacts: bool | None = None
    only_aliases: bool | None = None


class VacationResponseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    is_active: bool
    subject: str | None
    body: str | None
    start_at: datetime | None
    end_at: datetime | None
    only_contacts: bool
    only_aliases: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Catch-all schemas
# ---------------------------------------------------------------------------

class CatchAllCreate(BaseModel):
    target_mailbox_id: uuid.UUID


# ---------------------------------------------------------------------------
# Calendar event schemas
# ---------------------------------------------------------------------------

class CalendarEventBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    start_at: datetime
    end_at: datetime | None = None
    all_day: bool = False
    location: str | None = Field(default=None, max_length=500)
    recurrence_rule: str | None = Field(default=None, max_length=500)


class CalendarEventCreate(CalendarEventBase):
    pass


class CalendarEventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    all_day: bool | None = None
    location: str | None = Field(default=None, max_length=500)
    recurrence_rule: str | None = Field(default=None, max_length=500)


class CalendarEventOut(CalendarEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Contact schemas
# ---------------------------------------------------------------------------

class ContactCreate(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    display_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    notes: str | None = None
    is_vip: bool = False


class ContactUpdate(BaseModel):
    email: str | None = None
    display_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    notes: str | None = None
    is_vip: bool | None = None


class ContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    email: str
    display_name: str | None
    first_name: str | None
    last_name: str | None
    phone: str | None
    notes: str | None
    is_vip: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Contact group schemas
# ---------------------------------------------------------------------------

class ContactGroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ContactGroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime


class ContactGroupMemberCreate(BaseModel):
    contact_id: uuid.UUID


class ContactGroupMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    group_id: uuid.UUID
    contact_id: uuid.UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# File schemas
# ---------------------------------------------------------------------------

class FileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    path: str = Field(min_length=1, max_length=500)
    size_bytes: int = 0
    mime_type: str | None = None
    folder: str | None = None


class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    name: str
    path: str
    size_bytes: int
    mime_type: str | None
    folder: str | None
    created_at: datetime
    updated_at: datetime


class FileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    folder: str | None = None
    mime_type: str | None = None


# ---------------------------------------------------------------------------
# Note schemas
# ---------------------------------------------------------------------------

class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str | None = None


class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    title: str
    content: str | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Passkey schemas
# ---------------------------------------------------------------------------

class PasskeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class PasskeyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)


class PasskeyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    credential_id: str
    public_key: str
    sign_count: int
    name: str
    created_at: datetime
    last_used_at: datetime | None


# ---------------------------------------------------------------------------
# App password schemas
# ---------------------------------------------------------------------------

class AppPasswordCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    permissions: list[str] = Field(default_factory=lambda: ["smtp", "imap"])


class AppPasswordUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    permissions: list[str] | None = None
    revoked: bool | None = None


class AppPasswordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    name: str
    permissions: list[str]
    created_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None


# ---------------------------------------------------------------------------
# Snooze schemas
# ---------------------------------------------------------------------------

class SnoozeCreate(BaseModel):
    subject_contains: str | None = None
    sender_address: str | None = None
    domain_name: str | None = None
    until: datetime


class SnoozeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    subject_contains: str | None
    sender_address: str | None
    domain_name: str | None
    until: datetime
    active: bool
    created_at: datetime


# ---------------------------------------------------------------------------
# Login log schemas
# ---------------------------------------------------------------------------

class LoginLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID | None
    ip_address: str | None
    user_agent: str | None
    success: bool
    location: str | None
    created_at: datetime


# ---------------------------------------------------------------------------
# Session schemas
# ---------------------------------------------------------------------------

class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    ip_address: str | None
    user_agent: str | None
    created_at: datetime
    last_active_at: datetime
    expires_at: datetime


# ---------------------------------------------------------------------------
# Webmail SSO
# ---------------------------------------------------------------------------

class WebmailTokenOut(BaseModel):
    token: str
    url: str


class WebmailSSOIn(BaseModel):
    token: str


class WebmailSSOOut(BaseModel):
    email: str
    password_hash: str


# ---------------------------------------------------------------------------
# Import job schemas
# ---------------------------------------------------------------------------

class ImportJobBase(BaseModel):
    server: str
    port: int = 993
    username: str
    password: str
    tls: bool = True
    batch_size: int = 100


class ImportJobCreate(ImportJobBase):
    pass


class ImportJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    server: str
    port: int
    username: str
    tls: bool
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    messages_imported: int
    errors: int
    error_log: str | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Export job schemas
# ---------------------------------------------------------------------------

class ExportJobBase(BaseModel):
    type: str


class ExportJobCreate(ExportJobBase):
    pass


class ExportJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    type: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    file_path: str | None
    file_size: int | None
    created_at: datetime
    updated_at: datetime
