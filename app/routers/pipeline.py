"""
Pipeline router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

from app.database import get_db

router = APIRouter()


class CreateDealRequest(BaseModel):
    """Request to create a deal"""
    lead_id: str
    name: str
    amount: int
    currency: Optional[str] = "USD"
    stage_id: Optional[str] = None
    expected_close_date: Optional[str] = None


@router.get("/stages")
async def list_pipeline_stages(db: AsyncSession = Depends(get_db)):
    """List pipeline stages"""
    try:
        logger.info("Listing pipeline stages")

        # In production, this would query from database
        # For now, return a mock response
        stages = [
            {"id": "stage_001", "name": "New", "order": 1, "win_probability": 10},
            {"id": "stage_002", "name": "Qualified", "order": 2, "win_probability": 30},
            {"id": "stage_003", "name": "Proposal", "order": 3, "win_probability": 60},
            {"id": "stage_004", "name": "Closed Won", "order": 4, "win_probability": 100},
        ]

        return {"total": len(stages), "stages": stages}

    except Exception as e:
        logger.error(f"Failed to list pipeline stages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deals")
async def create_deal(
    request: CreateDealRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a deal in the pipeline"""
    try:
        logger.info(f"Creating deal: {request.name}")

        # In production, this would save to database
        # For now, return a mock response
        deal = {
            "id": "deal_123",
            "lead_id": request.lead_id,
            "name": request.name,
            "amount": request.amount,
            "currency": request.currency,
            "stage_id": request.stage_id,
            "expected_close_date": request.expected_close_date,
            "is_won": False,
            "is_lost": False,
            "created_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Deal created: {deal['id']}")
        return deal

    except Exception as e:
        logger.error(f"Failed to create deal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deals/{deal_id}")
async def get_deal(deal_id: str, db: AsyncSession = Depends(get_db)):
    """Get deal details"""
    try:
        logger.info(f"Getting deal details for {deal_id}")

        # In production, this would query from database
        # For now, return a mock response
        deal = {
            "id": deal_id,
            "name": "Acme Corp Renewal",
            "amount": 25000,
            "currency": "USD",
            "stage_id": "stage_003",
            "is_won": False,
            "is_lost": False,
            "created_at": datetime.utcnow().isoformat()
        }

        return deal

    except Exception as e:
        logger.error(f"Failed to get deal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deals")
async def list_deals(
    stage_id: Optional[str] = None,
    is_won: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List deals"""
    try:
        logger.info("Listing deals")

        # In production, this would query from database with filters
        # For now, return a mock response
        deals = [
            {"id": "deal_001", "name": "Acme Corp Renewal", "amount": 25000, "stage_id": "stage_003"},
            {"id": "deal_002", "name": "Tech Corp Expansion", "amount": 12000, "stage_id": "stage_002"},
        ]

        return {
            "total": len(deals),
            "deals": deals,
            "filters": {"stage_id": stage_id, "is_won": is_won},
            "pagination": {"limit": limit, "offset": offset}
        }

    except Exception as e:
        logger.error(f"Failed to list deals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deals/{deal_id}/move")
async def move_deal_stage(
    deal_id: str,
    stage_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Move a deal to a different pipeline stage"""
    try:
        logger.info(f"Moving deal {deal_id} to stage {stage_id}")

        # In production, this would update database
        # For now, return a mock response
        deal = {
            "id": deal_id,
            "stage_id": stage_id,
            "updated_at": datetime.utcnow().isoformat()
        }

        return deal

    except Exception as e:
        logger.error(f"Failed to move deal: {e}")
        raise HTTPException(status_code=500, detail=str(e))
