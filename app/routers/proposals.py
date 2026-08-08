"""
Proposals router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

from app.database import get_db

router = APIRouter()


class CreateProposalRequest(BaseModel):
    """Request to create a proposal"""
    lead_id: str
    title: str
    amount: int
    currency: Optional[str] = "USD"
    description: Optional[str] = None
    valid_until: Optional[str] = None


@router.post("/")
async def create_proposal(
    request: CreateProposalRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a proposal"""
    try:
        logger.info(f"Creating proposal: {request.title}")

        # In production, this would save to database
        # For now, return a mock response
        proposal = {
            "id": "proposal_123",
            "lead_id": request.lead_id,
            "title": request.title,
            "amount": request.amount,
            "currency": request.currency,
            "status": "draft",
            "valid_until": request.valid_until,
            "created_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Proposal created: {proposal['id']}")
        return proposal

    except Exception as e:
        logger.error(f"Failed to create proposal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{proposal_id}/send")
async def send_proposal(proposal_id: str, db: AsyncSession = Depends(get_db)):
    """Send a proposal to the lead"""
    try:
        logger.info(f"Sending proposal {proposal_id}")

        # In production, this would update database and trigger delivery
        # For now, return a mock response
        proposal = {
            "id": proposal_id,
            "status": "sent",
            "sent_at": datetime.utcnow().isoformat()
        }

        return proposal

    except Exception as e:
        logger.error(f"Failed to send proposal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{proposal_id}")
async def get_proposal(proposal_id: str, db: AsyncSession = Depends(get_db)):
    """Get proposal details"""
    try:
        logger.info(f"Getting proposal details for {proposal_id}")

        # In production, this would query from database
        # For now, return a mock response
        proposal = {
            "id": proposal_id,
            "title": "Acme Corp Renewal",
            "amount": 25000,
            "currency": "USD",
            "status": "sent",
            "created_at": datetime.utcnow().isoformat()
        }

        return proposal

    except Exception as e:
        logger.error(f"Failed to get proposal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_proposals(
    lead_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List proposals"""
    try:
        logger.info("Listing proposals")

        # In production, this would query from database with filters
        # For now, return a mock response
        proposals = [
            {"id": "proposal_001", "title": "Acme Corp Renewal", "amount": 25000, "status": "sent"},
            {"id": "proposal_002", "title": "Tech Corp Expansion", "amount": 12000, "status": "draft"},
        ]

        return {
            "total": len(proposals),
            "proposals": proposals,
            "filters": {"lead_id": lead_id, "status": status},
            "pagination": {"limit": limit, "offset": offset}
        }

    except Exception as e:
        logger.error(f"Failed to list proposals: {e}")
        raise HTTPException(status_code=500, detail=str(e))
