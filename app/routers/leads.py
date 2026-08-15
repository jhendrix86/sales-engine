"""
Lead router - real DB-backed CRUD against the leads table.
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
from app.models.lead import Lead, LeadStatus, LeadSource
from app.models.pipeline import Deal, PipelineStage
from app.models.tenant_base import apply_tenant_context

router = APIRouter()


class CreateLeadRequest(BaseModel):
    """Request to create lead"""
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    source: Optional[LeadSource] = None
    estimated_value: Optional[int] = None
    assigned_rep: Optional[str] = None


class ConvertLeadRequest(BaseModel):
    """Request to convert a lead into a deal"""
    deal_name: Optional[str] = None
    stage_id: Optional[str] = None


def _serialize(lead: Lead) -> dict:
    return {
        "id": str(lead.id),
        "name": lead.name,
        "email": lead.email,
        "phone": lead.phone,
        "company": lead.company,
        "title": lead.title,
        "status": lead.status.value,
        "source": lead.source.value if lead.source else None,
        "estimated_value": lead.estimated_value,
        "actual_value": lead.actual_value,
        "pipeline_stage": lead.pipeline_stage,
        "assigned_rep": lead.assigned_rep,
        "crm_contact_id": lead.crm_contact_id,
        "crm_deal_id": lead.crm_deal_id,
        "created_at": lead.created_at.isoformat(),
        "closed_at": lead.closed_at.isoformat() if lead.closed_at else None,
    }


async def _get_lead_or_404(db: AsyncSession, lead_id: str) -> Lead:
    try:
        lead_uuid = uuid.UUID(lead_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Lead '{lead_id}' not found")

    lead = await db.get(Lead, lead_uuid)
    if lead is None:
        raise HTTPException(status_code=404, detail=f"Lead '{lead_id}' not found")
    return lead


@router.post("/create")
async def create_lead(request: CreateLeadRequest, db: AsyncSession = Depends(get_db)):
    """Create a sales lead"""
    try:
        logger.info(f"Creating lead: {request.name}")

        lead = Lead(
            name=request.name,
            email=request.email,
            phone=request.phone,
            company=request.company,
            title=request.title,
            status=LeadStatus.NEW,
            source=request.source,
            estimated_value=request.estimated_value,
            assigned_rep=request.assigned_rep,
            pipeline_stage="new",
        )
        apply_tenant_context(lead)

        db.add(lead)
        await db.commit()
        await db.refresh(lead)

        logger.info(f"Lead created: {lead.id}")
        return _serialize(lead)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{lead_id}/convert")
async def convert_lead(lead_id: str, request: ConvertLeadRequest = ConvertLeadRequest(), db: AsyncSession = Depends(get_db)):
    """Convert a lead into a real deal in the pipeline"""
    try:
        lead = await _get_lead_or_404(db, lead_id)
        logger.info(f"Converting lead {lead_id} to a deal")

        stage = None
        if request.stage_id:
            try:
                stage = await db.get(PipelineStage, uuid.UUID(request.stage_id))
            except ValueError:
                stage = None
            if stage is None:
                raise HTTPException(status_code=404, detail=f"Pipeline stage '{request.stage_id}' not found")
        else:
            result = await db.execute(select(PipelineStage).where(PipelineStage.name == "Qualified"))
            stage = result.scalars().first()

        deal = Deal(
            lead_id=lead.id,
            name=request.deal_name or f"{lead.company or lead.name} Deal",
            amount=lead.estimated_value or 0,
            stage_id=stage.id if stage else None,
        )
        apply_tenant_context(deal)
        db.add(deal)

        lead.status = LeadStatus.QUALIFIED
        lead.pipeline_stage = stage.name.lower() if stage else "qualified"

        await db.commit()
        await db.refresh(lead)
        await db.refresh(deal)

        logger.info(f"Lead converted: {lead_id} -> deal {deal.id}")
        return {
            "id": str(lead.id),
            "status": lead.status.value,
            "pipeline_stage": lead.pipeline_stage,
            "deal_id": str(deal.id),
            "converted_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to convert lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{lead_id}")
async def get_lead(lead_id: str, db: AsyncSession = Depends(get_db)):
    """Get lead details"""
    try:
        lead = await _get_lead_or_404(db, lead_id)
        return _serialize(lead)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_leads(
    status: Optional[LeadStatus] = None,
    source: Optional[LeadSource] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List leads, real filters applied against the database"""
    try:
        query = select(Lead)
        if status is not None:
            query = query.where(Lead.status == status)
        if source is not None:
            query = query.where(Lead.source == source)

        query = query.order_by(Lead.created_at.desc()).offset(offset).limit(limit)

        result = await db.execute(query)
        leads = result.scalars().all()

        return {
            "total": len(leads),
            "leads": [_serialize(l) for l in leads],
            "filters": {"status": status.value if status else None, "source": source.value if source else None},
            "pagination": {"limit": limit, "offset": offset},
        }

    except Exception as e:
        logger.error(f"Failed to list leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))
