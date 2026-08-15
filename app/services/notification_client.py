"""
Real delivery of a proposal to its lead, via notification-engine's real
/notifications/send endpoint (made real earlier this session) - rather
than sales-engine building its own second email client, it reuses the
fleet's actual notification delivery layer, matching how monitoring-
engine's health polling reaches other engines over real HTTP.
"""

from dataclasses import dataclass
from typing import Optional

import httpx
from loguru import logger

from app.config import settings


@dataclass
class NotifyResult:
    success: bool
    error: Optional[str] = None


async def send_proposal_email(recipient_email: str, subject: str, message: str) -> NotifyResult:
    url = f"{settings.notification_engine_url.rstrip('/')}/notifications/send"
    payload = {"recipient": recipient_email, "recipient_type": "email", "channels": ["email"], "subject": subject, "message": message}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload)
    except httpx.HTTPError as exc:
        logger.warning(f"notification-engine request failed: {exc}")
        return NotifyResult(success=False, error=f"notification-engine request failed: {exc}")

    if response.status_code != 200:
        return NotifyResult(success=False, error=f"notification-engine returned {response.status_code}: {response.text[:300]}")

    body = response.json()
    if body.get("status") != "sent":
        return NotifyResult(success=False, error=body.get("error_message") or "notification-engine reported the send failed")

    return NotifyResult(success=True)
