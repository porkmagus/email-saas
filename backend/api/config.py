import os
import secrets
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/email_saas"
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    impersonate_token_expire_minutes: int = 15
    admin_2fa_required: bool = True
    environment: str = "development"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Stripe
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id: str = ""

    # Stalwart
    stalwart_base_url: str = "http://localhost:8080"
    stalwart_api_token: str = ""
    vps2_public_ip: str = "1.2.3.4"  # Set to VPS-2 public IP for SPF records

    # Frontend
    frontend_url: str = "http://localhost:5173"

    # API Docs
    docs_enabled: bool = False  # Set to True in dev, False in production

    # API Key HMAC
    api_key_secret: str = ""  # REQUIRED in production, no runtime default

    # Outbound Send Limits
    new_account_daily_limit: int = 25
    warmed_account_daily_limit: int = 500
    probation_days: int = 30
    hourly_limit_ratio: float = 0.1
    contabo_max_per_minute: int = 25

    # Mail / Notifications
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    notification_from: str = "noreply@example.com"
    slack_webhook_url: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
