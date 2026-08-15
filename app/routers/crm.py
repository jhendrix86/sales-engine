"""
CRM integration router - real DB-backed CRUD, and /sync performs a real
outbound call to the connected CRM (app/services/crm_client.py).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.crm import CRMContact, CRMIntegration, CRMSyncStatus, CRMType
from app.models.tenant_base import apply_tenant_context
from app.services.crm_client import fetch_contacts

router = APIRouter()


class CreateCRMIntegrationRequest(BaseModel):
    """Request to connect a CRM"""
    crm_type: CRMType
    crm_name: str
    api_key: Optional[str] = None
    api_url: Optional[str] = None


def _serialize(integration: CRMIntegration) -> dict:
    return {
        "id": str(integration.id),
        "crm_type": integration.crm_type.value,
        "crm_name": integration.crm_name,
        "api_url": integration.api_url,
        "sync_status": integration.sync_status.value,
        "last_sync_at": integration.last_sync_at.isoformat() if integration.last_sync_at else None,
        "last_error": integration.last_error,
        "created_at": integration.created_at.isoformat(),
    }


async def _get_integration_or_404(db: AsyncSession, integration_id: str) -> CRMIntegration:
    try:
        integration_uuid = uuid.UUID(integration_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"CRM integration '{integration_id}' not found")

    integration = await db.get(CRMIntegration, integration_uuid)
    if integration is None:
        raise HTTPException(status_code=404, detail=f"CRM integration '{integration_id}' not found")
    return integration


@router.post("/integrations")
async def create_crm_integration(request: CreateCRMIntegrationRequest, db: AsyncSession = Depends(get_db)):
    """Connect a CRM integration"""
    try:
        logger.info(f"Creating CRM integration: {request.crm_type.value}")

        integration = CRMIntegration(
            crm_type=request.crm_type,
            crm_name=request.crm_name,
            api_key=request.api_key,
            api_url=request.api_url,
            sync_status=CRMSyncStatus.ACTIVE,
        )
        apply_tenant_context(integration)

        db.add(integration)
        await db.commit()
        await db.refresh(integration)

        logger.info(f"CRM integration created: {integration.id}")
        return _serialize(integration)

    except Exception as e:
        logger.error(f"Failed to create CRM integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integrations")
async def list_crm_integrations(db: AsyncSession = Depends(get_db)):
    """List CRM integrations"""
    try:
        result = await db.execute(select(CRMIntegration).order_by(CRMIntegration.created_at.desc()))
        integrations = result.scalars().all()
        return {"total": len(integrations), "integrations": [_serialize(i) for i in integrations]}

    except Exception as e:
        logger.error(f"Failed to list CRM integrations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/integrations/{integration_id}/sync")
async def sync_crm_integration(integration_id: str, db: AsyncSession = Depends(get_db)):
    """
    Trigger a real CRM sync - pulls contacts from the actual provider API
    using this integration's own credentials. Reports a real fetched
    count and an honest failure if the provider call fails; does not
    speculatively create Lead/CRMContact rows from unmatched CRM records
    (that's a real lead-matching feature, out of scope for making this
    endpoint's HTTP call real rather than fabricated).
    """
    try:
        integration = await _get_integration_or_404(db, integration_id)
        logger.info(f"Syncing CRM integration {integration_id} ({integration.crm_type.value})")

        result = await fetch_contacts(integration.crm_type, integration.api_key, integration.api_url)

        integration.last_sync_at = datetime.utcnow()
        if result.success:
            integration.sync_status = CRMSyncStatus.ACTIVE
            integration.last_error = None
        else:
            integration.sync_status = CRMSyncStatus.ERROR
            integration.last_error = result.error

        await db.commit()
        await db.refresh(integration)

        logger.info(f"CRM sync {'succeeded' if result.success else 'failed'}: {integration_id}")
        return {
            "id": str(integration.id),
            "sync_status": integration.sync_status.value,
            "contacts_fetched": len(result.contacts) if result.success else 0,
            "error": result.error,
            "last_sync_at": integration.last_sync_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync CRM integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contacts")
async def list_crm_contacts(
    lead_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List synced CRM contacts, real query against the database"""
    try:
        query = select(CRMContact)
        if lead_id is not None:
            try:
                query = query.where(CRMContact.lead_id == uuid.UUID(lead_id))
            except ValueError:
                return {"total": 0, "contacts": [], "filters": {"lead_id": lead_id}, "pagination": {"limit": limit, "offset": offset}}

        query = query.order_by(CRMContact.created_at.desc()).offset(offset).limit(limit)

        result = await db.execute(query)
        contacts = result.scalars().all()

        return {
            "total": len(contacts),
            "contacts": [
                {
                    "id": str(c.id),
                    "lead_id": str(c.lead_id),
                    "crm_integration_id": str(c.crm_integration_id),
                    "crm_contact_id": c.crm_contact_id,
                    "sync_status": c.sync_status.value,
                }
                for c in contacts
            ],
            "filters": {"lead_id": lead_id},
            "pagination": {"limit": limit, "offset": offset},
        }

    except Exception as e:
        logger.error(f"Failed to list CRM contacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
