"""
Sales analytics router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
from loguru import logger

from app.database import get_db

router = APIRouter()


@router.get("/pipeline-summary")
async def get_pipeline_summary(db: AsyncSession = Depends(get_db)):
    """Get a summary of the sales pipeline"""
    try:
        logger.info("Getting pipeline summary")

        # In production, this would aggregate from database
        # For now, return a mock response
        summary = {
            "total_deals": 24,
            "total_value": 340000,
            "currency": "USD",
            "by_stage": [
                {"stage": "New", "count": 8, "value": 60000},
                {"stage": "Qualified", "count": 9, "value": 120000},
                {"stage": "Proposal", "count": 5, "value": 110000},
                {"stage": "Closed Won", "count": 2, "value": 50000},
            ]
        }

        return {"timestamp": datetime.utcnow().isoformat(), "summary": summary}

    except Exception as e:
        logger.error(f"Failed to get pipeline summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversion-rates")
async def get_conversion_rates(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get lead-to-deal conversion rates"""
    try:
        logger.info("Getting conversion rates")

        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = datetime.utcnow().isoformat()

        # In production, this would compute from database
        # For now, return a mock response
        rates = {
            "lead_to_qualified": 42.5,
            "qualified_to_proposal": 55.0,
            "proposal_to_won": 30.0,
            "overall_win_rate": 18.7
        }

        return {
            "period": {"start_date": start_date, "end_date": end_date},
            "rates": rates
        }

    except Exception as e:
        logger.error(f"Failed to get conversion rates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rep-performance")
async def get_rep_performance(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Get sales rep performance leaderboard"""
    try:
        logger.info("Getting sales rep performance")

        # In production, this would aggregate from database
        # For now, return a mock response
        reps = [
            {"rep_id": "rep_001", "name": "Alex Rivera", "deals_won": 6, "revenue": 95000},
            {"rep_id": "rep_002", "name": "Sam Chen", "deals_won": 4, "revenue": 62000},
        ]

        return {"total": len(reps), "reps": reps[:limit]}

    except Exception as e:
        logger.error(f"Failed to get rep performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))
