import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    LargeBinary,
    String,
    Text,
    UUID,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class AccountRole(str, enum.Enum):
    customer = "customer"
    admin = "admin"
    superadmin = "superadmin"


class AccountStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"
    cancelled = "cancelled"
    pending = "pending"


class PlanTier(str, enum.Enum):
    starter = "starter"
    pro = "pro"
    enterprise = "enterprise"


class TicketStatus(str, enum.Enum):
    open = "open"
    waiting_customer = "waiting_customer"
    waiting_staff = "waiting_staff"
    resolved = "resolved"
    closed = "closed"


class TicketPriority(str, enum.Enum):
    low = "low"
    normal = "normal"
    high = "high"
    critical = "critical"


class TicketCategory(str, enum.Enum):
    billing = "billing"
    setup = "setup"
    delivery = "delivery"
    account = "account"
    other = "other"


class JobType(str, enum.Enum):
    provision_account = "provision_account"
    add_domain = "add_domain"
    add_mailbox = "add_mailbox"
    delete_mailbox = "delete_mailbox"
    suspend_account = "suspend_account"
    delete_account = "delete_account"


class JobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    retrying = "retrying"


class ActorType(str, enum.Enum):
    user = "user"
    admin = "admin"
    system = "system"
    impersonation = "impersonation"


class SubscriptionStatus(str, enum.Enum):
    active = "active"
    past_due = "past_due"
    cancelled = "cancelled"
    trialing = "trialing"
    unpaid = "unpaid"


class MeteringEventType(str, enum.Enum):
    emails_sent = "emails_sent"
    storage_bytes = "storage_bytes"
    bandwidth_bytes = "bandwidth_bytes"


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        Index("ix_accounts_email", "email", unique=True),
        Index("ix_accounts_stripe_customer_id", "stripe_customer_id", unique=False),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus, name="account_status"), default=AccountStatus.pending, nullable=False
    )
    plan: Mapped[PlanTier] = mapped_column(
        Enum(PlanTier, name="plan_tier"), default=PlanTier.starter, nullable=False
    )
    role: Mapped[AccountRole] = mapped_column(
        Enum(AccountRole, name="account_role"), default=AccountRole.customer, nullable=False
    )
    totp_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recovery_codes: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sieve_script: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False
    )

    domains: Mapped[list["Domain"]] = relationship(
        "Domain", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    mailboxes: Mapped[list["Mailbox"]] = relationship(
        "Mailbox", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    provisioning_jobs: Mapped[list["ProvisioningJob"]] = relationship(
        "ProvisioningJob", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    api_keys: Mapped[list["ApiKey"]] = relationship(
        "ApiKey", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", foreign_keys="AuditLog.account_id", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    metering_events: Mapped[list["MeteringEvent"]] = relationship(
        "MeteringEvent", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    aliases: Mapped[list["Alias"]] = relationship(
        "Alias", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    blocked_senders: Mapped[list["BlockedSender"]] = relationship(
        "BlockedSender", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    email_rules: Mapped[list["EmailRule"]] = relationship(
        "EmailRule", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    vacation_response: Mapped["VacationResponse | None"] = relationship(
        "VacationResponse", back_populates="account", lazy="selectin", cascade="all, delete-orphan", uselist=False
    )
    contacts: Mapped[list["Contact"]] = relationship(
        "Contact", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    contact_groups: Mapped[list["ContactGroup"]] = relationship(
        "ContactGroup", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    files: Mapped[list["File"]] = relationship(
        "File", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    notes: Mapped[list["Note"]] = relationship(
        "Note", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    outbox_messages: Mapped[list["OutboxMessage"]] = relationship(
        "OutboxMessage", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    snoozes: Mapped[list["Snooze"]] = relationship(
        "Snooze", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    passkeys: Mapped[list["Passkey"]] = relationship(
        "Passkey", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    app_passwords: Mapped[list["AppPassword"]] = relationship(
        "AppPassword", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    login_logs: Mapped[list["LoginLog"]] = relationship(
        "LoginLog", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    calendar_events: Mapped[list["CalendarEvent"]] = relationship(
        "CalendarEvent", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    import_jobs: Mapped[list["ImportJob"]] = relationship(
        "ImportJob", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    export_jobs: Mapped[list["ExportJob"]] = relationship(
        "ExportJob", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )
    webmail_tokens: Mapped[list["WebmailToken"]] = relationship(
        "WebmailToken", back_populates="account", lazy="selectin", cascade="all, delete-orphan"
    )


class Domain(Base):
    __tablename__ = "domains"
    __table_args__ = (
        Index("ix_domains_account_id", "account_id"),
        Index("ix_domains_domain", "domain", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    domain: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mx_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    spf_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dkim_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dkim_selector: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mx_record: Mapped[str | None] = mapped_column(String(255), nullable=True)
    spf_record: Mapped[str | None] = mapped_column(Text, nullable=True)
    dkim_record: Mapped[str | None] = mapped_column(Text, nullable=True)
    dkim_private_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    catch_all_target_mailbox_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mailboxes.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False
    )

    account: Mapped["Account"] = relationship("Account", back_populates="domains")
    mailboxes: Mapped[list["Mailbox"]] = relationship(
        "Mailbox", back_populates="domain", lazy="selectin", cascade="all, delete-orphan",
        foreign_keys="Mailbox.domain_id"
    )
    aliases: Mapped[list["Alias"]] = relationship(
        "Alias", back_populates="domain", lazy="selectin", cascade="all, delete-orphan"
    )
    catch_all_target_mailbox: Mapped["Mailbox | None"] = relationship("Mailbox", foreign_keys=[catch_all_target_mailbox_id])


class Mailbox(Base):
    __tablename__ = "mailboxes"
    __table_args__ = (
        Index("ix_mailboxes_account_id", "account_id"),
        Index("ix_mailboxes_domain_id", "domain_id"),
        Index("ix_mailboxes_local_part_domain_id", "local_part", "domain_id", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    domain_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("domains.id", ondelete="CASCADE"), nullable=False
    )
    local_part: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    quota_bytes: Mapped[int] = mapped_column(Integer, default=1073741824, nullable=False)  # 1GB
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus, name="mailbox_status"), default=AccountStatus.active, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False
    )

    account: Mapped["Account"] = relationship("Account", back_populates="mailboxes")
    domain: Mapped["Domain"] = relationship("Domain", back_populates="mailboxes", foreign_keys="Mailbox.domain_id")


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        Index("ix_subscriptions_account_id", "account_id"),
        Index("ix_subscriptions_stripe_subscription_id", "stripe_subscription_id", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    stripe_subscription_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status"), default=SubscriptionStatus.active, nullable=False
    )
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    plan: Mapped[PlanTier] = mapped_column(
        Enum(PlanTier, name="subscription_plan_tier"), default=PlanTier.starter, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False
    )

    account: Mapped["Account"] = relationship("Account", back_populates="subscriptions")


class ProvisioningJob(Base):
    __tablename__ = "provisioning_jobs"
    __table_args__ = (
        Index("ix_provisioning_jobs_account_id", "account_id"),
        Index("ix_provisioning_jobs_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[JobType] = mapped_column(
        Enum(JobType, name="job_type"), nullable=False
    )
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status"), default=JobStatus.pending, nullable=False
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    account: Mapped["Account"] = relationship("Account", back_populates="provisioning_jobs")


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        Index("ix_tickets_account_id", "account_id"),
        Index("ix_tickets_status", "status"),
        Index("ix_tickets_priority", "priority"),
        Index("ix_tickets_assigned_to", "assigned_to"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticket_status"), default=TicketStatus.open, nullable=False
    )
    priority: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority, name="ticket_priority"), default=TicketPriority.normal, nullable=False
    )
    category: Mapped[TicketCategory] = mapped_column(
        Enum(TicketCategory, name="ticket_category"), default=TicketCategory.other, nullable=False
    )
    assigned_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False
    )

    account: Mapped["Account"] = relationship("Account", back_populates="tickets")
    comments: Mapped[list["TicketComment"]] = relationship(
        "TicketComment", back_populates="ticket", lazy="selectin", cascade="all, delete-orphan", order_by="TicketComment.created_at"
    )


class TicketComment(Base):
    __tablename__ = "ticket_comments"
    __table_args__ = (
        Index("ix_ticket_comments_ticket_id", "ticket_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True
    )
    author_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="comments")
    author: Mapped["Account | None"] = relationship("Account")


class ApiKey(Base):
    __tablename__ = "api_keys"
    __table_args__ = (
        Index("ix_api_keys_account_id", "account_id"),
        Index("ix_api_keys_prefix", "prefix"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    hashed_secret: Mapped[str] = mapped_column(Text, nullable=False)
    permissions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    account: Mapped["Account"] = relationship("Account", back_populates="api_keys")


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_log_account_id", "account_id"),
        Index("ix_audit_log_actor_id", "actor_id"),
        Index("ix_audit_log_resource_type_resource_id", "resource_type", "resource_id"),
        Index("ix_audit_log_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=True
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True
    )
    actor_type: Mapped[ActorType] = mapped_column(
        Enum(ActorType, name="actor_type"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    account: Mapped["Account | None"] = relationship("Account", foreign_keys=[account_id], back_populates="audit_logs")


class Suppression(Base):
    __tablename__ = "suppressions"
    __table_args__ = (
        Index("ix_suppressions_email", "email", unique=True),
        Index("ix_suppressions_domain", "domain"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)  # hard_bounce, spam_complaint, manual
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)


class MeteringEvent(Base):
    __tablename__ = "metering_events"
    __table_args__ = (
        Index("ix_metering_events_account_id", "account_id"),
        Index("ix_metering_events_event_type", "event_type"),
        Index("ix_metering_events_period_start", "period_start"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[MeteringEventType] = mapped_column(
        Enum(MeteringEventType, name="metering_event_type"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    account: Mapped["Account"] = relationship("Account", back_populates="metering_events")


class StripeEventStatus(str, enum.Enum):
    received = "received"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    retrying = "retrying"


class StripeEvent(Base):
    __tablename__ = "stripe_events"
    __table_args__ = (
        Index("ix_stripe_events_stripe_event_id", "stripe_event_id", unique=True),
        Index("ix_stripe_events_event_type", "event_type"),
        Index("ix_stripe_events_account_id", "account_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    stripe_event_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False)
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True
    )
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    processing_status: Mapped[StripeEventStatus] = mapped_column(
        Enum(StripeEventStatus, name="stripe_event_status"), default=StripeEventStatus.received, nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    account: Mapped["Account | None"] = relationship("Account")


class SendEventStatus(str, enum.Enum):
    sent = "sent"
    bounced = "bounced"
    complained = "complained"
    deferred = "deferred"
    rejected = "rejected"


class SendEvent(Base):
    __tablename__ = "send_events"
    __table_args__ = (
        Index("ix_send_events_account_id", "account_id"),
        Index("ix_send_events_domain_id", "domain_id"),
        Index("ix_send_events_mailbox_id", "mailbox_id"),
        Index("ix_send_events_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    domain_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("domains.id", ondelete="SET NULL"), nullable=True
    )
    mailbox_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mailboxes.id", ondelete="SET NULL"), nullable=True
    )
    recipient_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recipient_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[SendEventStatus] = mapped_column(
        Enum(SendEventStatus, name="send_event_status"), default=SendEventStatus.sent, nullable=False
    )
    message_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_attachments: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    account: Mapped["Account"] = relationship("Account")
    domain: Mapped["Domain | None"] = relationship("Domain")
    mailbox: Mapped["Mailbox | None"] = relationship("Mailbox")


class AbuseScoreStatus(str, enum.Enum):
    green = "green"
    yellow = "yellow"
    orange = "orange"
    red = "red"


class AbuseScore(Base):
    __tablename__ = "abuse_scores"
    __table_args__ = (
        Index("ix_abuse_scores_account_id", "account_id", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    bounce_rate: Mapped[float] = mapped_column(default=0.0, nullable=False)
    complaint_rate: Mapped[float] = mapped_column(default=0.0, nullable=False)
    failed_auth_rate: Mapped[float] = mapped_column(default=0.0, nullable=False)
    send_spike_score: Mapped[float] = mapped_column(default=0.0, nullable=False)
    suspicious_recipient_score: Mapped[float] = mapped_column(default=0.0, nullable=False)
    blacklist_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_score: Mapped[float] = mapped_column(default=0.0, nullable=False)
    status: Mapped[AbuseScoreStatus] = mapped_column(
        Enum(AbuseScoreStatus, name="abuse_score_status"), default=AbuseScoreStatus.green, nullable=False
    )
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False
    )

    account: Mapped["Account"] = relationship("Account")


class OutboundLimitPeriod(str, enum.Enum):
    hourly = "hourly"
    daily = "daily"
    monthly = "monthly"


class OutboundLimit(Base):
    __tablename__ = "outbound_limits"
    __table_args__ = (
        Index("ix_outbound_limits_account_id", "account_id"),
        Index("ix_outbound_limits_domain_id", "domain_id"),
        Index("ix_outbound_limits_mailbox_id", "mailbox_id"),
        Index("ix_outbound_limits_period_start", "period_start"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    domain_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("domains.id", ondelete="CASCADE"), nullable=True
    )
    mailbox_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mailboxes.id", ondelete="CASCADE"), nullable=True
    )
    period: Mapped[OutboundLimitPeriod] = mapped_column(
        Enum(OutboundLimitPeriod, name="outbound_limit_period"), nullable=False
    )
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    emails_sent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    emails_allowed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_reset_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    account: Mapped["Account"] = relationship("Account")
    domain: Mapped["Domain | None"] = relationship("Domain")
    mailbox: Mapped["Mailbox | None"] = relationship("Mailbox")


class MaintenanceWindow(Base):
    __tablename__ = "maintenance_windows"
    __table_args__ = (
        Index("ix_maintenance_windows_start_at", "start_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="scheduled", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False
    )


class Alias(Base):
    __tablename__ = "aliases"
    __table_args__ = (
        Index("ix_aliases_account_id", "account_id"),
        Index("ix_aliases_domain_id", "domain_id"),
        Index("ix_aliases_local_part_domain_id", "local_part", "domain_id", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    domain_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("domains.id", ondelete="CASCADE"), nullable=False
    )
    local_part: Mapped[str] = mapped_column(String(255), nullable=False)
    target_mailbox_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mailboxes.id", ondelete="CASCADE"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False
    )

    account: Mapped["Account"] = relationship("Account", back_populates="aliases")
    domain: Mapped["Domain"] = relationship("Domain", back_populates="aliases")
    target_mailbox: Mapped["Mailbox"] = relationship("Mailbox")


class BlockedSender(Base):
    __tablename__ = "blocked_senders"
    __table_args__ = (
        Index("ix_blocked_senders_account_id", "account_id"),
        Index("ix_blocked_senders_email_domain", "email_or_domain"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    email_or_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    is_domain: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    account: Mapped["Account"] = relationship("Account", back_populates="blocked_senders")


class EmailRuleField(str, enum.Enum):
    from_field = "from"
    to_field = "to"
    subject = "subject"
    body = "body"


class EmailRuleOperator(str, enum.Enum):
    contains = "contains"
    equals = "equals"
    starts_with = "starts_with"
    ends_with = "ends_with"


class EmailRuleActionType(str, enum.Enum):
    move_to = "move_to"
    copy_to = "copy_to"
    delete = "delete"
    mark_read = "mark_read"
    label = "label"


class EmailRule(Base):
    __tablename__ = "email_rules"
    __table_args__ = (
        Index("ix_email_rules_account_id", "account_id"),
        Index("ix_email_rules_priority", "priority"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    custom_sieve: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False
    )

    account: Mapped["Account"] = relationship("Account", back_populates="email_rules")
    conditions: Mapped[list["EmailRuleCondition"]] = relationship(
        "EmailRuleCondition", back_populates="rule", lazy="selectin", cascade="all, delete-orphan"
    )
    actions: Mapped[list["EmailRuleAction"]] = relationship(
        "EmailRuleAction", back_populates="rule", lazy="selectin", cascade="all, delete-orphan"
    )


class EmailRuleCondition(Base):
    __tablename__ = "email_rule_conditions"
    __table_args__ = (
        Index("ix_email_rule_conditions_rule_id", "rule_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("email_rules.id", ondelete="CASCADE"), nullable=False
    )
    field: Mapped[EmailRuleField] = mapped_column(
        Enum(EmailRuleField, name="email_rule_field"), nullable=False
    )
    operator: Mapped[EmailRuleOperator] = mapped_column(
        Enum(EmailRuleOperator, name="email_rule_operator"), nullable=False
    )
    value: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    rule: Mapped["EmailRule"] = relationship("EmailRule", back_populates="conditions")


class EmailRuleAction(Base):
    __tablename__ = "email_rule_actions"
    __table_args__ = (
        Index("ix_email_rule_actions_rule_id", "rule_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("email_rules.id", ondelete="CASCADE"), nullable=False
    )
    action_type: Mapped[EmailRuleActionType] = mapped_column(
        Enum(EmailRuleActionType, name="email_rule_action_type"), nullable=False
    )
    target_mailbox_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mailboxes.id", ondelete="SET NULL"), nullable=True
    )
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    rule: Mapped["EmailRule"] = relationship("EmailRule", back_populates="actions")
    target_mailbox: Mapped["Mailbox | None"] = relationship("Mailbox")


class VacationResponse(Base):
    __tablename__ = "vacation_responses"
    __table_args__ = (
        Index("ix_vacation_responses_account_id", "account_id", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    only_contacts: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    only_aliases: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False
    )

    account: Mapped["Account"] = relationship("Account", back_populates="vacation_response")


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (
        Index("ix_contacts_account_id", "account_id"),
        Index("ix_contacts_email", "email"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False
    )

    account: Mapped["Account"] = relationship("Account", back_populates="contacts")
    group_memberships: Mapped[list["ContactGroupMember"]] = relationship(
        "ContactGroupMember", back_populates="contact", lazy="selectin", cascade="all, delete-orphan"
    )


class ContactGroup(Base):
    __tablename__ = "contact_groups"
    __table_args__ = (
        Index("ix_contact_groups_account_id", "account_id"),
        Index("ix_contact_groups_name", "name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False
    )

    account: Mapped["Account"] = relationship("Account", back_populates="contact_groups")
    members: Mapped[list["ContactGroupMember"]] = relationship(
        "ContactGroupMember", back_populates="group", lazy="selectin", cascade="all, delete-orphan"
    )


class ContactGroupMember(Base):
    __tablename__ = "contact_group_members"
    __table_args__ = (
        Index("ix_contact_group_members_group_id", "group_id"),
        Index("ix_contact_group_members_contact_id", "contact_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contact_groups.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    group: Mapped["ContactGroup"] = relationship("ContactGroup", back_populates="members")
    contact: Mapped["Contact"] = relationship("Contact", back_populates="group_memberships")


class File(Base):
    __tablename__ = "files"
    __table_args__ = (
        Index("ix_files_account_id", "account_id"),
        Index("ix_files_folder", "folder"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    folder: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False
    )

    account: Mapped["Account"] = relationship("Account", back_populates="files")


class Note(Base):
    __tablename__ = "notes"
    __table_args__ = (
        Index("ix_notes_account_id", "account_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False
    )

    account: Mapped["Account"] = relationship("Account", back_populates="notes")


class OutboxMessageStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    cancelled = "cancelled"


class OutboxMessage(Base):
    __tablename__ = "outbox_messages"
    __table_args__ = (
        Index("ix_outbox_messages_account_id", "account_id"),
        Index("ix_outbox_messages_scheduled_at", "scheduled_at"),
        Index("ix_outbox_messages_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    from_address: Mapped[str] = mapped_column(String(255), nullable=False)
    to_addresses: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    text_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    html_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[OutboxMessageStatus] = mapped_column(
        Enum(OutboxMessageStatus, name="outbox_message_status"), default=OutboxMessageStatus.pending, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    account: Mapped["Account"] = relationship("Account", back_populates="outbox_messages")


class Snooze(Base):
    __tablename__ = "snoozes"
    __table_args__ = (
        Index("ix_snoozes_account_id", "account_id"),
        Index("ix_snoozes_active", "active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    subject_contains: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sender_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    domain_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    account: Mapped["Account"] = relationship("Account", back_populates="snoozes")


class Passkey(Base):
    __tablename__ = "passkeys"
    __table_args__ = (
        Index("ix_passkeys_account_id", "account_id"),
        Index("ix_passkeys_credential_id", "credential_id", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    credential_id: Mapped[str] = mapped_column(String(500), nullable=False)
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    sign_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    account: Mapped["Account"] = relationship("Account", back_populates="passkeys")


class AppPassword(Base):
    __tablename__ = "app_passwords"
    __table_args__ = (
        Index("ix_app_passwords_account_id", "account_id"),
        Index("ix_app_passwords_hashed_password", "hashed_password"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    permissions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    account: Mapped["Account"] = relationship("Account", back_populates="app_passwords")


class LoginLog(Base):
    __tablename__ = "login_logs"
    __table_args__ = (
        Index("ix_login_logs_account_id", "account_id"),
        Index("ix_login_logs_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    account: Mapped["Account | None"] = relationship("Account", back_populates="login_logs")


class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        Index("ix_sessions_account_id", "account_id"),
        Index("ix_sessions_token_jti", "token_jti"),
        Index("ix_sessions_expires_at", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    token_jti: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    last_active_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    account: Mapped["Account"] = relationship("Account", back_populates="sessions")


class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    __table_args__ = (
        Index("ix_calendar_events_account_id", "account_id"),
        Index("ix_calendar_events_start_at", "start_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    all_day: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    recurrence_rule: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False
    )

    account: Mapped["Account"] = relationship("Account", back_populates="calendar_events")


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_account_id", "account_id"),
        Index("ix_messages_folder", "folder"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    from_addr: Mapped[str] = mapped_column(String(255), nullable=False)
    body_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    folder: Mapped[str] = mapped_column(String(50), default="inbox", nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    account: Mapped["Account"] = relationship("Account", back_populates="messages")


class ImportJob(Base):
    __tablename__ = "import_jobs"
    __table_args__ = (
        Index("ix_import_jobs_account_id", "account_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    server: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, default=993, nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str] = mapped_column(Text, nullable=False)
    tls: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    messages_imported: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False
    )

    account: Mapped["Account"] = relationship("Account", back_populates="import_jobs")


class ExportJob(Base):
    __tablename__ = "export_jobs"
    __table_args__ = (
        Index("ix_export_jobs_account_id", "account_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False
    )

    account: Mapped["Account"] = relationship("Account", back_populates="export_jobs")


class WebmailToken(Base):
    __tablename__ = "webmail_tokens"
    __table_args__ = (
        Index("ix_webmail_tokens_account_id", "account_id"),
        Index("ix_webmail_tokens_token", "token", unique=True),
        Index("ix_webmail_tokens_expires_at", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    account: Mapped["Account"] = relationship("Account", back_populates="webmail_tokens")
