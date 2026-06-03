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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False
    )

    account: Mapped["Account"] = relationship("Account", back_populates="domains")
    mailboxes: Mapped[list["Mailbox"]] = relationship(
        "Mailbox", back_populates="domain", lazy="selectin", cascade="all, delete-orphan"
    )


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
    domain: Mapped["Domain"] = relationship("Domain", back_populates="mailboxes")


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
