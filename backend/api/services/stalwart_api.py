import httpx
from api.config import get_settings

settings = get_settings()

client = httpx.AsyncClient(
    base_url=settings.stalwart_base_url,
    headers={"Authorization": f"Bearer {settings.stalwart_api_token}"},
    timeout=30.0,
)


async def create_domain(domain: str):
    try:
        r = await client.post("/api/v1/domain", json={"name": domain, "type": "primary"})
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        raise RuntimeError(f"Stalwart create_domain failed: {e}")


async def create_mailbox(address: str, password: str, quota: int | None = None):
    try:
        payload = {
            "address": address,
            "password": password,
            "type": "individual",
            "quota": quota,
        }
        r = await client.post("/api/v1/account", json=payload)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        raise RuntimeError(f"Stalwart create_mailbox failed: {e}")


async def delete_mailbox(address: str):
    try:
        r = await client.delete(f"/api/v1/account/{address}")
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        raise RuntimeError(f"Stalwart delete_mailbox failed: {e}")


async def get_server_health():
    try:
        r = await client.get("/api/v1/health")
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        return {"status": "error", "detail": str(e)}


async def queue_message(
    from_address: str,
    to_addresses: list[str],
    subject: str,
    text_body: str,
    html_body: str | None = None,
):
    """Queue a message via Stalwart's API.
    In production, this uses SMTP or JMAP submission.
    """
    try:
        payload = {
            "from": from_address,
            "to": to_addresses,
            "subject": subject,
            "textBody": text_body,
        }
        if html_body:
            payload["htmlBody"] = html_body
        r = await client.post("/api/v1/queue", json=payload)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        raise RuntimeError(f"Stalwart queue_message failed: {e}")


async def get_queue_metrics():
    """Get live queue metrics from Stalwart."""
    try:
        r = await client.get("/api/v1/queue")
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        return {"error": str(e), "queue_depth": -1}


async def configure_dkim(domain: str, selector: str, private_key: str, public_key: str):
    """Configure DKIM signing for a domain in Stalwart.
    In production, this pushes the private key to Stalwart's signing config.
    """
    try:
        payload = {
            "domain": domain,
            "selector": selector,
            "privateKey": private_key,
            "publicKey": public_key,
        }
        r = await client.post("/api/v1/dkim", json=payload)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError as e:
        raise RuntimeError(f"Stalwart configure_dkim failed: {e}")
