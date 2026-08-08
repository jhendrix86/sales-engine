"""
CRM integration router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

from app.database import get_db

router = APIRouter()


class CreateCRMIntegrationRequest(BaseModel):
    """Request to connect a CRM"""
    crm_type: str
    crm_name: str
    api_key: Optional[str] = None
    api_url: Optional[str] = None


@router.post("/integrations")
async def create_crm_integration(
    request: CreateCRMIntegrationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Connect a CRM integration"""
    try:
        logger.info(f"Creating CRM integration: {request.crm_type}")

        # In production, this would save to database
        # For now, return a mock response
        integration = {
            "id": "crm_int_123",
            "crm_type": request.crm_type,
            "crm_name": request.crm_name,
            "sync_status": "active",
            "created_at": datetime.utcnow().isoformat()
        }

        logger.info(f"CRM integration created: {integration['id']}")
        return integration

    except Exception as e:
        logger.error(f"Failed to create CRM integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integrations")
async def list_crm_integrations(db: AsyncSession = Depends(get_db)):
    """List CRM integrations"""
    try:
        logger.info("Listing CRM integrations")

        # In production, this would query from database
        # For now, return a mock response
        integrations = [
            {"id": "crm_int_001", "crm_type": "hubspot", "sync_status": "active"},
            {"id": "crm_int_002", "crm_type": "salesforce", "sync_status": "paused"},
        ]

        return {"total": len(integrations), "integrations": integrations}

    except Exception as e:
        logger.error(f"Failed to list CRM integrations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/integrations/{integration_id}/sync")
async def sync_crm_integration(integration_id: str, db: AsyncSession = Depends(get_db)):
    """Trigger a CRM sync"""
    try:
        logger.info(f"Syncing CRM integration {integration_id}")

        # In production, this would push/pull records via the CRM's API
        # For now, return a mock response
        result = {
            "id": integration_id,
            "sync_status": "active",
            "contacts_synced": 0,
            "last_sync_at": datetime.utcnow().isoformat()
        }

        return result

    except Exception as e:
        logger.error(f"Failed to sync CRM integration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contacts")
async def list_crm_contacts(
    lead_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List synced CRM contacts"""
    try:
        logger.info("Listing CRM contacts")

        # In production, this would query from database with filters
        # For now, return a mock response
        contacts = [
            {"id": "contact_001", "lead_id": "lead_001", "crm_contact_id": "0031t000", "sync_status": "synced"},
        ]

        return {
            "total": len(contacts),
            "contacts": contacts,
            "filters": {"lead_id": lead_id},
            "pagination": {"limit": limit, "offset": offset}
        }

    except Exception as e:
        logger.error(f"Failed to list CRM contacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
