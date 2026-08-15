"""
Real CRM contact-list clients for the 3 providers this engine's schema
anticipates (CRMType). Raw httpx calls to each provider's real REST API,
not their SDK packages - same convention as every other real client
built in this fleet this session (SendGrid/Twilio/Slack in
notification-engine, the generic sync client in integration-engine).

Credentials come from the CRMIntegration row itself (api_key/api_url),
not global Settings - each integration owns its own connection,
matching the schema design (multiple integrations of the same crm_type
are possible, each with different credentials).
"""

from dataclasses import dataclass, field
from typing import Optional

import httpx
from loguru import logger

from app.models.crm import CRMType


@dataclass
class CRMSyncResult:
    success: bool
    contacts: list = field(default_factory=list)
    error: Optional[str] = None


async def _fetch_hubspot_contacts(api_key: Optional[str], api_url: Optional[str]) -> CRMSyncResult:
    if not api_key:
        return CRMSyncResult(success=False, error="No api_key configured for this HubSpot integration")

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                "https://api.hubapi.com/crm/v3/objects/contacts",
                headers={"Authorization": f"Bearer {api_key}"},
            )
    except httpx.HTTPError as exc:
        logger.warning(f"HubSpot request failed: {exc}")
        return CRMSyncResult(success=False, error=f"HubSpot request failed: {exc}")

    if response.status_code != 200:
        return CRMSyncResult(success=False, error=f"HubSpot returned {response.status_code}: {response.text[:300]}")

    results = response.json().get("results", [])
    contacts = [{"id": c.get("id"), "url": None} for c in results]
    return CRMSyncResult(success=True, contacts=contacts)


async def _fetch_salesforce_contacts(api_key: Optional[str], api_url: Optional[str]) -> CRMSyncResult:
    if not api_key or not api_url:
        return CRMSyncResult(success=False, error="Salesforce requires both api_key (session token) and api_url (instance URL)")

    url = f"{api_url.rstrip('/')}/services/data/v58.0/query"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
                params={"q": "SELECT Id, Name, Email FROM Contact"},
            )
    except httpx.HTTPError as exc:
        logger.warning(f"Salesforce request failed: {exc}")
        return CRMSyncResult(success=False, error=f"Salesforce request failed: {exc}")

    if response.status_code != 200:
        return CRMSyncResult(success=False, error=f"Salesforce returned {response.status_code}: {response.text[:300]}")

    records = response.json().get("records", [])
    contacts = [{"id": c.get("Id"), "url": f"{api_url.rstrip('/')}/{c.get('Id')}"} for c in records]
    return CRMSyncResult(success=True, contacts=contacts)


async def _fetch_pipedrive_contacts(api_key: Optional[str], api_url: Optional[str]) -> CRMSyncResult:
    if not api_key:
        return CRMSyncResult(success=False, error="No api_key configured for this Pipedrive integration")

    base_url = api_url.rstrip("/") if api_url else "https://api.pipedrive.com"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(f"{base_url}/api/v1/persons", params={"api_token": api_key})
    except httpx.HTTPError as exc:
        logger.warning(f"Pipedrive request failed: {exc}")
        return CRMSyncResult(success=False, error=f"Pipedrive request failed: {exc}")

    if response.status_code != 200:
        return CRMSyncResult(success=False, error=f"Pipedrive returned {response.status_code}: {response.text[:300]}")

    records = response.json().get("data") or []
    contacts = [{"id": c.get("id"), "url": None} for c in records]
    return CRMSyncResult(success=True, contacts=contacts)


_FETCHERS = {
    CRMType.HUBSPOT: _fetch_hubspot_contacts,
    CRMType.SALESFORCE: _fetch_salesforce_contacts,
    CRMType.PIPEDRIVE: _fetch_pipedrive_contacts,
}


async def fetch_contacts(crm_type: CRMType, api_key: Optional[str], api_url: Optional[str]) -> CRMSyncResult:
    """Real contact fetch from whichever CRM this integration is connected to."""
    fetcher = _FETCHERS.get(crm_type)
    if fetcher is None:
        return CRMSyncResult(success=False, error=f"Unsupported CRM type: {crm_type}")
    return await fetcher(api_key, api_url)
