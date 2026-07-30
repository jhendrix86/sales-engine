"""
Lead router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.lead import Lead, LeadStatus, LeadSource

router = APIRouter()


class CreateLeadRequest(BaseModel):
    """Request to create lead"""
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    source: Optional[str] = None
    estimated_value: Optional[int] = None


@router.post("/create")
async def create_lead(
    request: CreateLeadRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a sales lead"""
    try:
        logger.info(f"Creating lead: {request.name}")
        
        # In production, this would save to database
        # For now, return a mock response
        lead = {
            "id": "lead_123",
            "name": request.name,
            "email": request.email,
            "phone": request.phone,
            "company": request.company,
            "title": request.title,
            "status": "new",
            "source": request.source,
            "estimated_value": request.estimated_value,
            "pipeline_stage": "new",
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Lead created: {lead['id']}")
        return lead
        
    except Exception as e:
        logger.error(f"Failed to create lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{lead_id}/convert")
async def convert_lead(
    lead_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Convert lead to opportunity"""
    try:
        logger.info(f"Converting lead {lead_id} to opportunity")
        
        # In production, this would update database
        # For now, return a mock response
        lead = {
            "id": lead_id,
            "status": "qualified",
            "pipeline_stage": "proposal",
            "converted_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Lead converted: {lead_id}")
        return lead
        
    except Exception as e:
        logger.error(f"Failed to convert lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{lead_id}")
async def get_lead(
    lead_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get lead details"""
    try:
        logger.info(f"Getting lead details for {lead_id}")
        
        # In production, this would query from database
        # For now, return a mock response
        lead = {
            "id": lead_id,
            "name": "John Doe",
            "email": "john@example.com",
            "company": "Acme Corp",
            "status": "qualified",
            "pipeline_stage": "proposal",
            "estimated_value": 10000,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return lead
        
    except Exception as e:
        logger.error(f"Failed to get lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_leads(
    status: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List leads"""
    try:
        logger.info("Listing leads")
        
        # In production, this would query from database with filters
        # For now, return a mock response
        leads = [
            {
                "id": "lead_001",
                "name": "John Doe",
                "email": "john@example.com",
                "company": "Acme Corp",
                "status": "qualified",
                "estimated_value": 10000
            },
            {
                "id": "lead_002",
                "name": "Jane Smith",
                "email": "jane@example.com",
                "company": "Tech Corp",
                "status": "new",
                "estimated_value": 5000
            }
        ]
        
        return {
            "total": len(leads),
            "leads": leads,
            "filters": {
                "status": status,
                "source": source
            },
            "pagination": {
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to list leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))
