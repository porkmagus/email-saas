#!/usr/bin/env python3
"""Stalwart staging integration smoke test.

Tests health, domain, DKIM, mailbox, message queue, and metrics endpoints.
Exits 0 on success, nonzero on failure.
"""

import asyncio
import sys
import uuid

from api.services.stalwart_api import (
    create_domain,
    create_mailbox,
    delete_mailbox,
    get_server_health,
    get_queue_metrics,
    queue_message,
    configure_dkim,
)


TEST_DOMAIN = f"smoke-{uuid.uuid4().hex[:8]}.test"
TEST_MAILBOX = f"test@{TEST_DOMAIN}"
TEST_PASSWORD = "SmokeTest123!"


async def main() -> int:
    errors = []

    # 1. Health
    try:
        health = await get_server_health()
        print(f"[1/7] Health: {health}")
    except Exception as e:
        errors.append(f"Health check failed: {e}")
        print(f"[1/7] Health FAILED: {e}")

    # 2. Create domain
    try:
        result = await create_domain(TEST_DOMAIN)
        print(f"[2/7] Create domain: {result}")
    except Exception as e:
        errors.append(f"Create domain failed: {e}")
        print(f"[2/7] Create domain FAILED: {e}")

    # 3. Configure DKIM
    try:
        result = await configure_dkim(
            TEST_DOMAIN,
            "saas20260101abcd",
            "-----BEGIN PRIVATE KEY-----\nMII...\n-----END PRIVATE KEY-----",
            "MIIB...",
        )
        print(f"[3/7] Configure DKIM: {result}")
    except Exception as e:
        errors.append(f"Configure DKIM failed: {e}")
        print(f"[3/7] Configure DKIM FAILED: {e}")

    # 4. Create mailbox
    try:
        result = await create_mailbox(TEST_MAILBOX, TEST_PASSWORD, quota=1073741824)
        print(f"[4/7] Create mailbox: {result}")
    except Exception as e:
        errors.append(f"Create mailbox failed: {e}")
        print(f"[4/7] Create mailbox FAILED: {e}")

    # 5. Queue message
    try:
        result = await queue_message(
            from_address=TEST_MAILBOX,
            to_addresses=["recipient@example.com"],
            subject="Smoke test",
            text_body="This is a smoke test message.",
        )
        print(f"[5/7] Queue message: {result}")
    except Exception as e:
        errors.append(f"Queue message failed: {e}")
        print(f"[5/7] Queue message FAILED: {e}")

    # 6. Fetch queue metrics
    try:
        result = await get_queue_metrics()
        print(f"[6/7] Queue metrics: {result}")
    except Exception as e:
        errors.append(f"Queue metrics failed: {e}")
        print(f"[6/7] Queue metrics FAILED: {e}")

    # 7. Delete mailbox
    try:
        result = await delete_mailbox(TEST_MAILBOX)
        print(f"[7/7] Delete mailbox: {result}")
    except Exception as e:
        errors.append(f"Delete mailbox failed: {e}")
        print(f"[7/7] Delete mailbox FAILED: {e}")

    if errors:
        print(f"\nFAILED: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("\nAll smoke tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
