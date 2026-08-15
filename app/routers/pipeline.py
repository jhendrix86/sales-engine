"""
Pipeline router - real DB-backed CRUD against pipeline_stages/deals.
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
from app.models.pipeline import Deal, PipelineStage
from app.models.tenant_base import apply_tenant_context

router = APIRouter()


class CreateDealRequest(BaseModel):
    """Request to create a deal"""
    lead_id: str
    name: str
    amount: int
    currency: Optional[str] = "USD"
    stage_id: Optional[str] = None
    expected_close_date: Optional[datetime] = None


def _serialize_stage(stage: PipelineStage) -> dict:
    return {"id": str(stage.id), "name": stage.name, "order": stage.order, "win_probability": stage.win_probability}


def _serialize_deal(deal: Deal) -> dict:
    return {
        "id": str(deal.id),
        "lead_id": str(deal.lead_id),
        "name": deal.name,
        "amount": deal.amount,
        "currency": deal.currency,
        "stage_id": str(deal.stage_id) if deal.stage_id else None,
        "expected_close_date": deal.expected_close_date.isoformat() if deal.expected_close_date else None,
        "is_won": deal.is_won,
        "is_lost": deal.is_lost,
        "created_at": deal.created_at.isoformat(),
        "closed_at": deal.closed_at.isoformat() if deal.closed_at else None,
    }


async def _get_deal_or_404(db: AsyncSession, deal_id: str) -> Deal:
    try:
        deal_uuid = uuid.UUID(deal_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Deal '{deal_id}' not found")

    deal = await db.get(Deal, deal_uuid)
    if deal is None:
        raise HTTPException(status_code=404, detail=f"Deal '{deal_id}' not found")
    return deal


@router.get("/stages")
async def list_pipeline_stages(db: AsyncSession = Depends(get_db)):
    """List pipeline stages, real query against the seeded stages"""
    try:
        result = await db.execute(select(PipelineStage).order_by(PipelineStage.order))
        stages = result.scalars().all()
        return {"total": len(stages), "stages": [_serialize_stage(s) for s in stages]}

    except Exception as e:
        logger.error(f"Failed to list pipeline stages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deals")
async def create_deal(request: CreateDealRequest, db: AsyncSession = Depends(get_db)):
    """Create a deal in the pipeline"""
    try:
        try:
            lead_uuid = uuid.UUID(request.lead_id)
        except ValueError:
            raise HTTPException(status_code=404, detail=f"Lead '{request.lead_id}' not found")

        lead = await db.get(Lead, lead_uuid)
        if lead is None:
            raise HTTPException(status_code=404, detail=f"Lead '{request.lead_id}' not found")

        stage = None
        if request.stage_id:
            try:
                stage = await db.get(PipelineStage, uuid.UUID(request.stage_id))
            except ValueError:
                stage = None
            if stage is None:
                raise HTTPException(status_code=404, detail=f"Pipeline stage '{request.stage_id}' not found")

        logger.info(f"Creating deal: {request.name}")

        deal = Deal(
            lead_id=lead.id,
            name=request.name,
            amount=request.amount,
            currency=request.currency,
            stage_id=stage.id if stage else None,
            expected_close_date=request.expected_close_date,
        )
        apply_tenant_context(deal)

        db.add(deal)
        await db.commit()
        await db.refresh(deal)

        logger.info(f"Deal created: {deal.id}")
        return _serialize_deal(deal)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create deal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deals/{deal_id}")
async def get_deal(deal_id: str, db: AsyncSession = Depends(get_db)):
    """Get deal details"""
    try:
        deal = await _get_deal_or_404(db, deal_id)
        return _serialize_deal(deal)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get deal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deals")
async def list_deals(
    stage_id: Optional[str] = None,
    is_won: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List deals, real filters applied against the database"""
    try:
        query = select(Deal)
        if stage_id is not None:
            try:
                query = query.where(Deal.stage_id == uuid.UUID(stage_id))
            except ValueError:
                return {"total": 0, "deals": [], "filters": {"stage_id": stage_id, "is_won": is_won}, "pagination": {"limit": limit, "offset": offset}}
        if is_won is not None:
            query = query.where(Deal.is_won == is_won)

        query = query.order_by(Deal.created_at.desc()).offset(offset).limit(limit)

        result = await db.execute(query)
        deals = result.scalars().all()

        return {
            "total": len(deals),
            "deals": [_serialize_deal(d) for d in deals],
            "filters": {"stage_id": stage_id, "is_won": is_won},
            "pagination": {"limit": limit, "offset": offset},
        }

    except Exception as e:
        logger.error(f"Failed to list deals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deals/{deal_id}/move")
async def move_deal_stage(deal_id: str, stage_id: str, db: AsyncSession = Depends(get_db)):
    """Move a deal to a different pipeline stage - real existence check on the target stage"""
    try:
        deal = await _get_deal_or_404(db, deal_id)

        try:
            stage_uuid = uuid.UUID(stage_id)
        except ValueError:
            raise HTTPException(status_code=404, detail=f"Pipeline stage '{stage_id}' not found")

        stage = await db.get(PipelineStage, stage_uuid)
        if stage is None:
            raise HTTPException(status_code=404, detail=f"Pipeline stage '{stage_id}' not found")

        logger.info(f"Moving deal {deal_id} to stage {stage_id}")

        deal.stage_id = stage.id
        await db.commit()
        await db.refresh(deal)

        return _serialize_deal(deal)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to move deal: {e}")
        raise HTTPException(status_code=500, detail=str(e))
