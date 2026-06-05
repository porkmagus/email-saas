import json
import httpx
from fastapi import HTTPException
from api.config import get_settings

settings = get_settings()

client = httpx.AsyncClient(
    base_url=settings.stalwart_base_url,
    headers={"Authorization": f"Bearer {settings.stalwart_api_token}"},
    timeout=30.0,
)

# Default admin account ID for management operations
# In Stalwart, the first admin account is typically 'b' after bootstrap
SYSTEM_ACCOUNT_ID = "b"

# Stalwart JMAP capability for management objects
STALWART_USING = [
    "urn:ietf:params:jmap:core",
    "urn:ietf:params:jmap:mail",
    "urn:ietf:params:jmap:principals",
    "urn:ietf:params:jmap:sieve",
    "urn:ietf:params:jmap:submission",
    "urn:stalwart:jmap",
]


async def jmap_call(method_calls: list, using: list[str] | None = None):
    """Make a JMAP API call via Stalwart's /jmap endpoint."""
    if using is None:
        using = STALWART_USING
    payload = {
        "using": using,
        "methodCalls": method_calls,
    }
    try:
        r = await client.post("/jmap", json=payload)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Mail server error: {e.response.status_code}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Mail server unreachable: {str(e)}")


async def get_domain_id(domain_name: str) -> str | None:
    """Look up the Stalwart domain ID for a given domain name."""
    method_calls = [
        ["x:Domain/query", {"accountId": SYSTEM_ACCOUNT_ID, "filter": {"name": domain_name}}, "0"],
    ]
    result = await jmap_call(method_calls)
    query_response = result.get("methodResponses", [])[0]
    if query_response[0] == "x:Domain/query":
        ids = query_response[1].get("ids", [])
        return ids[0] if ids else None
    return None


async def create_domain(domain: str) -> dict:
    """Create a domain in Stalwart via JMAP x:Domain/set."""
    try:
        method_calls = [
            [
                "x:Domain/set",
                {
                    "accountId": SYSTEM_ACCOUNT_ID,
                    "create": {
                        "newdomain": {
                            "@type": "Domain",
                            "name": domain,
                        }
                    },
                    "oldState": None,
                },
                "0",
            ],
        ]
        result = await jmap_call(method_calls)
        set_response = result.get("methodResponses", [])[0]
        if set_response[0] == "x:Domain/set":
            created = set_response[1].get("created", {})
            not_created = set_response[1].get("notCreated", {})
            if "newdomain" in created:
                return {"id": created["newdomain"]["id"], "name": domain}
            elif "newdomain" in not_created:
                error = not_created["newdomain"]
                raise RuntimeError(f"Stalwart create_domain failed: {error.get('type', 'unknown')} - {error.get('description', 'No details')}")
        return result
    except httpx.HTTPError as e:
        raise RuntimeError(f"Stalwart create_domain failed: {e}")


async def delete_domain(domain_id: str):
    """Delete a domain in Stalwart via JMAP x:Domain/set."""
    try:
        method_calls = [
            [
                "x:Domain/set",
                {
                    "accountId": SYSTEM_ACCOUNT_ID,
                    "destroy": [domain_id],
                    "oldState": None,
                },
                "0",
            ],
        ]
        result = await jmap_call(method_calls)
        set_response = result.get("methodResponses", [])[0]
        if set_response[0] == "x:Domain/set":
            not_destroyed = set_response[1].get("notDestroyed", {})
            if domain_id in not_destroyed:
                error = not_destroyed[domain_id]
                raise RuntimeError(f"Stalwart delete_domain failed: {error.get('type', 'unknown')} - {error.get('description', 'No details')}")
        return result
    except httpx.HTTPError as e:
        raise RuntimeError(f"Stalwart delete_domain failed: {e}")


async def create_mailbox(address: str, password: str, quota: int | None = None):
    """Create a mailbox (account) in Stalwart via JMAP x:Account/set."""
    try:
        # Split address into local part and domain
        local_part, domain = address.split("@", 1)
        domain_id = await get_domain_id(domain)
        if not domain_id:
            raise RuntimeError(f"Domain '{domain}' not found in Stalwart")

        payload = {
            "@type": "User",
            "name": local_part,
            "domainId": domain_id,
            "credentials": {
                "0": {
                    "@type": "Password",
                    "secret": password,
                }
            },
        }
        if quota:
            # Quota is not supported in x:Account/set create
            # It must be set separately or managed by Stalwart defaults
            pass

        method_calls = [
            [
                "x:Account/set",
                {
                    "accountId": SYSTEM_ACCOUNT_ID,
                    "create": {"newuser": payload},
                    "oldState": None,
                },
                "0",
            ],
        ]
        result = await jmap_call(method_calls)
        set_response = result.get("methodResponses", [])[0]
        if set_response[0] == "x:Account/set":
            created = set_response[1].get("created", {})
            not_created = set_response[1].get("notCreated", {})
            if "newuser" in created:
                return {"id": created["newuser"]["id"], "address": address}
            elif "newuser" in not_created:
                error = not_created["newuser"]
                raise RuntimeError(f"Stalwart create_mailbox failed: {error.get('type', 'unknown')} - {error.get('description', 'No details')}")
        return result
    except httpx.HTTPError as e:
        raise RuntimeError(f"Stalwart create_mailbox failed: {e}")


async def delete_mailbox(account_id: str):
    """Delete a mailbox (account) in Stalwart via JMAP x:Account/set."""
    try:
        method_calls = [
            [
                "x:Account/set",
                {
                    "accountId": SYSTEM_ACCOUNT_ID,
                    "destroy": [account_id],
                    "oldState": None,
                },
                "0",
            ],
        ]
        result = await jmap_call(method_calls)
        set_response = result.get("methodResponses", [])[0]
        if set_response[0] == "x:Account/set":
            not_destroyed = set_response[1].get("notDestroyed", {})
            if account_id in not_destroyed:
                error = not_destroyed[account_id]
                raise RuntimeError(f"Stalwart delete_mailbox failed: {error.get('type', 'unknown')} - {error.get('description', 'No details')}")
        return result
    except httpx.HTTPError as e:
        raise RuntimeError(f"Stalwart delete_mailbox failed: {e}")


async def create_alias_in_stalwart(alias_address: str, target_address: str):
    """Create an alias as a Stalwart group account."""
    try:
        local_part, domain = alias_address.split("@", 1)
        domain_id = await get_domain_id(domain)
        if not domain_id:
            raise RuntimeError(f"Domain '{domain}' not found in Stalwart")

        method_calls = [
            [
                "x:Account/set",
                {
                    "accountId": SYSTEM_ACCOUNT_ID,
                    "create": {
                        "newalias": {
                            "@type": "Group",
                            "name": local_part,
                            "domainId": domain_id,
                            "members": [target_address],
                        }
                    },
                    "oldState": None,
                },
                "0",
            ],
        ]
        result = await jmap_call(method_calls)
        set_response = result.get("methodResponses", [])[0]
        if set_response[0] == "x:Account/set":
            created = set_response[1].get("created", {})
            if "newalias" in created:
                return {"id": created["newalias"]["id"], "address": alias_address}
            elif "newalias" in set_response[1].get("notCreated", {}):
                error = set_response[1]["notCreated"]["newalias"]
                raise RuntimeError(f"Stalwart create_alias failed: {error.get('type', 'unknown')} - {error.get('description', 'No details')}")
        return result
    except httpx.HTTPError as e:
        raise RuntimeError(f"Stalwart create_alias failed: {e}")


async def delete_alias_in_stalwart(alias_id: str):
    """Delete a Stalwart group alias."""
    return await delete_mailbox(alias_id)


async def list_principals():
    """List all Stalwart principals (users, groups, aliases)."""
    method_calls = [
        ["x:Account/query", {"accountId": SYSTEM_ACCOUNT_ID, "filter": {}}, "0"],
    ]
    result = await jmap_call(method_calls)
    query_response = result.get("methodResponses", [])[0]
    if query_response[0] == "x:Account/query":
        ids = query_response[1].get("ids", [])
        if ids:
            get_calls = [
                ["x:Account/get", {"accountId": SYSTEM_ACCOUNT_ID, "ids": ids}, "0"],
            ]
            return await jmap_call(get_calls)
    return result


async def get_server_health():
    """Get server health via JMAP session."""
    try:
        r = await client.get("/jmap/session")
        r.raise_for_status()
        data = r.json()
        return {"status": "ok", "capabilities": list(data.get("capabilities", {}).keys())}
    except httpx.HTTPError as e:
        return {"status": "error", "detail": str(e)}


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
            f"/jmap/upload/{account_id}",
            headers={"Content-Type": "application/sieve"},
            content=script.encode("utf-8"),
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


async def queue_message(
    from_address: str,
    to_addresses: list[str],
    subject: str,
    text_body: str,
    html_body: str | None = None,
):
    """Queue a message via Stalwart's JMAP EmailSubmission/set."""
    try:
        # Build email data
        body_values = {"1": {"value": text_body, "type": "text/plain"}}
        text_body_parts = [{"partId": "1", "type": "text/plain"}]
        email_data = {
            "from": [{"email": from_address}],
            "to": [{"email": addr} for addr in to_addresses],
            "subject": subject,
            "textBody": text_body_parts,
            "bodyValues": body_values,
        }
        if html_body:
            body_values["2"] = {"value": html_body, "type": "text/html"}
            email_data["htmlBody"] = [{"partId": "2", "type": "text/html"}]

        # Create email in mailbox
        create_email = {
            "newEmail": {
                "mailboxIds": {"a": True},
                "keywords": {"$seen": True},
                **email_data,
            }
        }

        method_calls = [
            ["Email/set", {"accountId": "b", "create": create_email}, "0"],
        ]
        result = await jmap_call(method_calls)

        # Submit for delivery
        email_set_response = result.get("methodResponses", [])[0]
        if email_set_response[0] == "Email/set":
            created = email_set_response[1].get("created", {})
            if "newEmail" in created:
                email_id = created["newEmail"]["id"]
                # Get identity
                identity_calls = [
                    ["Identity/get", {"accountId": "b", "ids": None}, "0"],
                ]
                identity_result = await jmap_call(identity_calls)
                identity_response = identity_result.get("methodResponses", [])[0]
                if identity_response[0] == "Identity/get":
                    identities = identity_response[1].get("list", [])
                    identity_id = identities[0]["id"] if identities else None
                    if identity_id:
                        submit_calls = [
                            ["EmailSubmission/set", {
                                "accountId": "b",
                                "create": {
                                    "newSubmission": {
                                        "emailId": email_id,
                                        "identityId": identity_id,
                                    }
                                }
                            }, "0"],
                        ]
                        return await jmap_call(submit_calls)
        return result
    except httpx.HTTPError as e:
        raise RuntimeError(f"Stalwart queue_message failed: {e}")


async def get_queue_metrics():
    """Get live queue metrics from Stalwart via JMAP."""
    try:
        method_calls = [
            ["Email/query", {"accountId": "b", "filter": {}}, "0"],
        ]
        result = await jmap_call(method_calls)
        return {"queue_depth": len(result.get("methodResponses", [])[0][1].get("ids", [])), "error": None}
    except httpx.HTTPError as e:
        return {"error": str(e), "queue_depth": -1}


async def configure_dkim(domain: str, selector: str, private_key: str, public_key: str):
    """Configure DKIM signing for a domain in Stalwart.
    NOTE: DKIM management in Stalwart is automatic. This is a placeholder.
    """
    raise RuntimeError(
        "Stalwart manages DKIM automatically. Please configure DKIM via the Stalwart admin web UI."
    )


# JMAP helper methods for email operations
async def get_mailbox_list(account_id: str = "b"):
    """Get the list of mailboxes for an account."""
    method_calls = [
        ["Mailbox/get", {"accountId": account_id, "ids": None}, "0"],
    ]
    return await jmap_call(method_calls)


async def get_email_list(account_id: str = "b", mailbox_id: str | None = None, limit: int = 50):
    """Get the list of emails for an account or mailbox."""
    filter_spec = {}
    if mailbox_id:
        filter_spec["inMailbox"] = mailbox_id
    method_calls = [
        ["Email/query", {"accountId": account_id, "filter": filter_spec, "limit": limit}, "0"],
    ]
    result = await jmap_call(method_calls)
    query_response = result.get("methodResponses", [])[0]
    if query_response[0] == "Email/query":
        ids = query_response[1].get("ids", [])
        if ids:
            get_calls = [
                ["Email/get", {"accountId": account_id, "ids": ids, "properties": ["id", "subject", "from", "to", "receivedAt", "size"]}, "0"],
            ]
            return await jmap_call(get_calls)
    return result


async def get_email_body(account_id: str, email_id: str):
    """Get the full body of an email."""
    method_calls = [
        ["Email/get", {"accountId": account_id, "ids": [email_id], "properties": ["id", "subject", "from", "to", "receivedAt", "size", "textBody", "htmlBody", "bodyValues", "attachments"], "fetchTextBodyValues": True, "fetchHTMLBodyValues": True}, "0"],
    ]
    return await jmap_call(method_calls)


async def send_email(
    account_id: str,
    from_address: str,
    to_addresses: list[str],
    subject: str,
    text_body: str,
    html_body: str | None = None,
):
    """Send an email via JMAP EmailSubmission/set."""
    body_values = {"1": {"value": text_body, "type": "text/plain"}}
    text_body_parts = [{"partId": "1", "type": "text/plain"}]
    if html_body:
        body_values["2"] = {"value": html_body, "type": "text/html"}
        text_body_parts = [{"partId": "1", "type": "text/plain"}]
    email_data = {
        "from": [{"email": from_address}],
        "to": [{"email": addr} for addr in to_addresses],
        "subject": subject,
        "textBody": text_body_parts,
        "bodyValues": body_values,
    }
    if html_body:
        email_data["htmlBody"] = [{"partId": "2", "type": "text/html"}]

    create_email = {
        "newEmail": {
            "mailboxIds": {"a": True},
            "keywords": {"$seen": True},
            **email_data,
        }
    }

    method_calls = [
        ["Email/set", {"accountId": account_id, "create": create_email}, "0"],
    ]
    result = await jmap_call(method_calls)

    email_set_response = result.get("methodResponses", [])[0]
    if email_set_response[0] == "Email/set":
        created = email_set_response[1].get("created", {})
        if "newEmail" in created:
            email_id = created["newEmail"]["id"]
            identity_calls = [
                ["Identity/get", {"accountId": account_id, "ids": None}, "0"],
            ]
            identity_result = await jmap_call(identity_calls)
            identity_response = identity_result.get("methodResponses", [])[0]
            if identity_response[0] == "Identity/get":
                identities = identity_response[1].get("list", [])
                identity_id = identities[0]["id"] if identities else None
                if identity_id:
                    submit_calls = [
                        ["EmailSubmission/set", {
                            "accountId": account_id,
                            "create": {
                                "newSubmission": {
                                    "emailId": email_id,
                                    "identityId": identity_id,
                                }
                            }
                        }, "0"],
                    ]
                    return await jmap_call(submit_calls)
    return result
