import stripe
from api.config import get_settings

settings = get_settings()

if settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key


async def create_customer(email: str, metadata: dict | None = None):
    return stripe.Customer.create(email=email, metadata=metadata or {})


async def create_refund(payment_intent: str, amount: int | None = None, reason: str | None = None):
    params = {"payment_intent": payment_intent, "reason": reason}
    if amount is not None:
        params["amount"] = amount
    return stripe.Refund.create(**params)


async def get_subscription(subscription_id: str):
    return stripe.Subscription.retrieve(subscription_id)
