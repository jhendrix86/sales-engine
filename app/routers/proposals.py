"""
Proposals router - real DB-backed CRUD, and /send actually delivers the
proposal via notification-engine's real email channel
(app/services/notification_client.py).
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
from app.models.lead import Lead
from app.models.proposal import Proposal, ProposalStatus
from app.models.tenant_base import apply_tenant_context
from app.services.notification_client import send_proposal_email

router = APIRouter()


class CreateProposalRequest(BaseModel):
    """Request to create a proposal"""
    lead_id: str
    title: str
    amount: int
    currency: Optional[str] = "USD"
    description: Optional[str] = None
    content: Optional[str] = None
    valid_until: Optional[datetime] = None


def _serialize(proposal: Proposal) -> dict:
    return {
        "id": str(proposal.id),
        "lead_id": str(proposal.lead_id),
        "title": proposal.title,
        "description": proposal.description,
        "amount": proposal.amount,
        "currency": proposal.currency,
        "status": proposal.status.value,
        "valid_until": proposal.valid_until.isoformat() if proposal.valid_until else None,
        "sent_at": proposal.sent_at.isoformat() if proposal.sent_at else None,
        "viewed_at": proposal.viewed_at.isoformat() if proposal.viewed_at else None,
        "delivery_error": proposal.delivery_error,
        "created_at": proposal.created_at.isoformat(),
    }


async def _get_proposal_or_404(db: AsyncSession, proposal_id: str) -> Proposal:
    try:
        proposal_uuid = uuid.UUID(proposal_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Proposal '{proposal_id}' not found")

    proposal = await db.get(Proposal, proposal_uuid)
    if proposal is None:
        raise HTTPException(status_code=404, detail=f"Proposal '{proposal_id}' not found")
    return proposal


@router.post("/")
async def create_proposal(request: CreateProposalRequest, db: AsyncSession = Depends(get_db)):
    """Create a proposal"""
    try:
        try:
            lead_uuid = uuid.UUID(request.lead_id)
        except ValueError:
            raise HTTPException(status_code=404, detail=f"Lead '{request.lead_id}' not found")

        lead = await db.get(Lead, lead_uuid)
        if lead is None:
            raise HTTPException(status_code=404, detail=f"Lead '{request.lead_id}' not found")

        logger.info(f"Creating proposal: {request.title}")

        proposal = Proposal(
            lead_id=lead.id,
            title=request.title,
            description=request.description,
            content=request.content,
            amount=request.amount,
            currency=request.currency,
            status=ProposalStatus.DRAFT,
            valid_until=request.valid_until,
        )
        apply_tenant_context(proposal)

        db.add(proposal)
        await db.commit()
        await db.refresh(proposal)

        logger.info(f"Proposal created: {proposal.id}")
        return _serialize(proposal)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create proposal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{proposal_id}/send")
async def send_proposal(proposal_id: str, db: AsyncSession = Depends(get_db)):
    """Send a proposal to the lead - a real delivery attempt via notification-engine"""
    try:
        proposal = await _get_proposal_or_404(db, proposal_id)
        lead = await db.get(Lead, proposal.lead_id)
        if lead is None:
            raise HTTPException(status_code=404, detail=f"Lead '{proposal.lead_id}' not found")

        logger.info(f"Sending proposal {proposal_id} to {lead.email}")

        message = proposal.content or proposal.description or f"Please find our proposal: {proposal.title}"
        result = await send_proposal_email(lead.email, f"Proposal: {proposal.title}", message)

        if result.success:
            proposal.status = ProposalStatus.SENT
            proposal.sent_at = datetime.utcnow()
            proposal.delivery_error = None
        else:
            proposal.delivery_error = result.error

        await db.commit()
        await db.refresh(proposal)

        logger.info(f"Proposal {proposal_id} delivery {'succeeded' if result.success else 'failed'}")
        return _serialize(proposal)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send proposal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{proposal_id}")
async def get_proposal(proposal_id: str, db: AsyncSession = Depends(get_db)):
    """Get proposal details"""
    try:
        proposal = await _get_proposal_or_404(db, proposal_id)
        return _serialize(proposal)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get proposal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_proposals(
    lead_id: Optional[str] = None,
    status: Optional[ProposalStatus] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List proposals, real filters applied against the database"""
    try:
        query = select(Proposal)
        if lead_id is not None:
            try:
                query = query.where(Proposal.lead_id == uuid.UUID(lead_id))
            except ValueError:
                return {"total": 0, "proposals": [], "filters": {"lead_id": lead_id, "status": None}, "pagination": {"limit": limit, "offset": offset}}
        if status is not None:
            query = query.where(Proposal.status == status)

        query = query.order_by(Proposal.created_at.desc()).offset(offset).limit(limit)

        result = await db.execute(query)
        proposals = result.scalars().all()

        return {
            "total": len(proposals),
            "proposals": [_serialize(p) for p in proposals],
            "filters": {"lead_id": lead_id, "status": status.value if status else None},
            "pagination": {"limit": limit, "offset": offset},
        }

    except Exception as e:
        logger.error(f"Failed to list proposals: {e}")
        raise HTTPException(status_code=500, detail=str(e))
