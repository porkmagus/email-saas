import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_db
from api.deps import get_current_active_account
from api.models import Account, EmailRule, EmailRuleCondition, EmailRuleAction
from api.schemas import (
    CustomSieveUpdate,
    EmailRuleCreate,
    EmailRuleOut,
    EmailRuleUpdate,
    MessageOut,
    SieveUpdate,
    SieveValidate,
    SieveValidateOut,
)
from api.services.audit import audit_from_request

router = APIRouter()

DEFAULT_SIEVE_TEMPLATE = '''require ["fileinto", "reject"];

# Add your Sieve rules below
'''


@router.post("", response_model=EmailRuleOut)
async def create_rule(
    request: Request,
    data: EmailRuleCreate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    rule = EmailRule(
        account_id=account.id,
        name=data.name,
        priority=data.priority,
    )
    db.add(rule)
    await db.flush()

    for c in data.conditions:
        cond = EmailRuleCondition(
            rule_id=rule.id,
            field=c.field,
            operator=c.operator,
            value=c.value,
        )
        db.add(cond)

    for a in data.actions:
        act = EmailRuleAction(
            rule_id=rule.id,
            action_type=a.action_type,
            target_mailbox_id=a.target_mailbox_id,
            label=a.label,
        )
        db.add(act)

    await db.commit()
    await db.refresh(rule)

    await audit_from_request(
        request, "create_email_rule", "email_rule", str(rule.id), account.id, account.id,
        metadata={"name": rule.name}
    )

    return rule


@router.get("", response_model=list[EmailRuleOut])
async def list_rules(
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(EmailRule).where(EmailRule.account_id == account.id).order_by(EmailRule.priority)
    )
    return result.scalars().all()


# ---------------------------------------------------------------------------
# Raw Sieve script endpoints (must come before /{rule_id} to avoid shadowing)
# ---------------------------------------------------------------------------

def _validate_sieve(script: str) -> list[str]:
    errors: list[str] = []
    stripped = script.strip()
    if not stripped:
        errors.append("Script is empty")
        return errors
    # Must start with require or if
    if not re.search(r'^(\s*require|\s*if)', stripped):
        errors.append("Script must start with 'require' or 'if'")
    # Security: disallow redirect
    if re.search(r'\bredirect\b', stripped, re.IGNORECASE):
        errors.append("The 'redirect' action is not allowed for security reasons")
    # Check balanced braces
    open_count = stripped.count('{')
    close_count = stripped.count('}')
    if open_count != close_count:
        errors.append(f"Unbalanced braces: {open_count} open, {close_count} close")
    return errors


@router.get("/sieve", response_model=dict)
async def get_sieve_script(
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    script = account.sieve_script
    if script is None:
        script = DEFAULT_SIEVE_TEMPLATE
    return {"script": script}


@router.put("/sieve", response_model=dict)
async def update_sieve_script(
    request: Request,
    data: SieveUpdate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    errors = _validate_sieve(data.script)
    if errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))
    account.sieve_script = data.script
    await db.commit()
    await db.refresh(account)
    await audit_from_request(
        request, "update_sieve_script", "account", str(account.id), account.id, account.id
    )
    return {"script": account.sieve_script}


@router.post("/sieve/validate", response_model=SieveValidateOut)
async def validate_sieve_script(
    data: SieveValidate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    errors = _validate_sieve(data.script)
    return SieveValidateOut(valid=len(errors) == 0, errors=errors)


# ---------------------------------------------------------------------------
# Individual rule endpoints
# ---------------------------------------------------------------------------

@router.get("/{rule_id}", response_model=EmailRuleOut)
async def get_rule(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(EmailRule).where(EmailRule.id == rule_id, EmailRule.account_id == account.id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.patch("/{rule_id}", response_model=EmailRuleOut)
async def update_rule(
    request: Request,
    rule_id: uuid.UUID,
    data: EmailRuleUpdate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(EmailRule).where(EmailRule.id == rule_id, EmailRule.account_id == account.id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    if data.name is not None:
        rule.name = data.name
    if data.priority is not None:
        rule.priority = data.priority
    if data.is_active is not None:
        rule.is_active = data.is_active

    if data.conditions is not None:
        # Delete old conditions and recreate
        for cond in rule.conditions:
            await db.delete(cond)
        for c in data.conditions:
            cond = EmailRuleCondition(
                rule_id=rule.id,
                field=c.field,
                operator=c.operator,
                value=c.value,
            )
            db.add(cond)

    if data.actions is not None:
        for act in rule.actions:
            await db.delete(act)
        for a in data.actions:
            act = EmailRuleAction(
                rule_id=rule.id,
                action_type=a.action_type,
                target_mailbox_id=a.target_mailbox_id,
                label=a.label,
            )
            db.add(act)

    await db.commit()
    await db.refresh(rule)

    await audit_from_request(
        request, "update_email_rule", "email_rule", str(rule.id), account.id, account.id,
        metadata={"name": rule.name, "is_active": rule.is_active}
    )

    return rule


@router.delete("/{rule_id}", response_model=MessageOut)
async def delete_rule(
    request: Request,
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(EmailRule).where(EmailRule.id == rule_id, EmailRule.account_id == account.id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    await db.delete(rule)
    await db.commit()

    await audit_from_request(
        request, "delete_email_rule", "email_rule", str(rule_id), account.id, account.id
    )

    return MessageOut(message="Rule deleted")


@router.patch("/{rule_id}/sieve", response_model=EmailRuleOut)
async def update_custom_sieve(
    request: Request,
    rule_id: uuid.UUID,
    data: CustomSieveUpdate,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_active_account),
):
    result = await db.execute(
        select(EmailRule).where(EmailRule.id == rule_id, EmailRule.account_id == account.id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    rule.custom_sieve = data.custom_sieve
    await db.commit()
    await db.refresh(rule)

    await audit_from_request(
        request, "update_custom_sieve", "email_rule", str(rule_id), account.id, account.id
    )

    return rule
