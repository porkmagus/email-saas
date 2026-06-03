import httpx
from fastapi import HTTPException
from api.config import get_settings

settings = get_settings()

client = httpx.AsyncClient(
    base_url=settings.stalwart_base_url,
    headers={"Authorization": f"Bearer {settings.stalwart_api_token}"},
    timeout=30.0,
)


async def jmap_call(method_calls: list, using: list[str] | None = None):
    """Make a JMAP API call via Stalwart's /api endpoint."""
    if using is None:
        using = [
            "urn:ietf:params:jmap:core",
            "urn:ietf:params:jmap:mail",
            "urn:ietf:params:jmap:sieve",
        ]
    payload = {
        "using": using,
        "methodCalls": method_calls,
    }
    try:
        r = await client.post("/api", json=payload)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Mail server error: {e.response.status_code}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Mail server unreachable: {str(e)}")


async def create_alias_in_stalwart(alias_address: str, target_address: str):
    """Create an alias as a Stalwart group principal."""
    try:
        payload = {
            "type": "group",
            "name": alias_address,
            "emails": [alias_address],
            "members": [target_address],
        }
        r = await client.post("/api/v1/principal", json=payload)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Stalwart create_alias failed: {e}")


async def delete_alias_in_stalwart(alias_address: str):
    """Delete a Stalwart group principal alias."""
    try:
        r = await client.delete(f"/api/v1/principal/{alias_address}")
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Stalwart delete_alias failed: {e}")


async def get_sieve_scripts(account_id: str):
    """List sieve scripts for an account via JMAP."""
    method_calls = [
        ["SieveScript/get", {"accountId": account_id}, "0"],
    ]
    return await jmap_call(method_calls)


async def set_sieve_script(account_id: str, name: str, blob: str, is_active: bool = True):
    """Push a sieve script via JMAP."""
    method_calls = [
        [
            "SieveScript/set",
            {
                "accountId": account_id,
                "create": {
                    name: {
                        "name": name,
                        "blobId": blob,
                        "isActive": is_active,
                    }
                },
            },
            "0",
        ],
    ]
    return await jmap_call(method_calls)


async def upload_sieve_blob(account_id: str, script: str) -> str:
    """Upload a sieve script as a blob and return blobId."""
    try:
        r = await client.post(
            f"/api/v1/blob",
            headers={"Content-Type": "application/sieve"},
            data=script.encode("utf-8"),
        )
        r.raise_for_status()
        data = r.json()
        return data.get("blobId", data.get("id"))
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Stalwart upload_sieve_blob failed: {e}")


async def delete_sieve_script(account_id: str, script_id: str):
    """Delete a sieve script via JMAP."""
    method_calls = [
        [
            "SieveScript/set",
            {
                "accountId": account_id,
                "destroy": [script_id],
            },
            "0",
        ],
    ]
    return await jmap_call(method_calls)


async def list_principals():
    """List all Stalwart principals (users, groups, aliases)."""
    try:
        r = await client.get("/api/v1/principal")
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Stalwart list_principals failed: {e}")


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
