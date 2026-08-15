"""
Sales analytics router - every endpoint now computes from real data
instead of returning fixed literals.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
from loguru import logger

from app.database import get_db
from app.models.lead import Lead, LeadStatus
from app.models.pipeline import Deal, PipelineStage

router = APIRouter()

# Rank used to compute stage-to-stage conversion - a lead "reached" a
# rank if its current status is that rank or later in the funnel.
# CLOSED_LOST shares CLOSED_WON's rank (both are terminal / "reached the
# end of the funnel") but is excluded from the win-rate numerator.
_STATUS_RANK = {
    LeadStatus.NEW: 0,
    LeadStatus.CONTACTED: 1,
    LeadStatus.QUALIFIED: 2,
    LeadStatus.PROPOSAL: 3,
    LeadStatus.NEGOTIATION: 4,
    LeadStatus.CLOSED_WON: 5,
    LeadStatus.CLOSED_LOST: 5,
}


@router.get("/pipeline-summary")
async def get_pipeline_summary(db: AsyncSession = Depends(get_db)):
    """Real aggregation of the active (not-lost) pipeline"""
    try:
        deals_result = await db.execute(select(Deal).where(Deal.is_lost == False))  # noqa: E712
        deals = deals_result.scalars().all()

        stages_result = await db.execute(select(PipelineStage))
        stage_names = {s.id: s.name for s in stages_result.scalars().all()}

        by_stage_totals: dict = {}
        for deal in deals:
            stage_name = stage_names.get(deal.stage_id, "Unassigned")
            bucket = by_stage_totals.setdefault(stage_name, {"count": 0, "value": 0})
            bucket["count"] += 1
            bucket["value"] += deal.amount or 0

        summary = {
            "total_deals": len(deals),
            "total_value": sum(d.amount or 0 for d in deals),
            "currency": "USD",
            "by_stage": [{"stage": name, **totals} for name, totals in by_stage_totals.items()],
        }

        return {"timestamp": datetime.utcnow().isoformat(), "summary": summary}

    except Exception as e:
        logger.error(f"Failed to get pipeline summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversion-rates")
async def get_conversion_rates(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    """Real lead-to-deal conversion rates computed from leads created in the window"""
    try:
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        result = await db.execute(select(Lead).where(Lead.created_at >= start_date, Lead.created_at <= end_date))
        leads = result.scalars().all()

        def reached(rank: int) -> int:
            return sum(1 for lead in leads if _STATUS_RANK[lead.status] >= rank)

        total = len(leads)
        reached_qualified = reached(_STATUS_RANK[LeadStatus.QUALIFIED])
        reached_proposal = reached(_STATUS_RANK[LeadStatus.PROPOSAL])
        won = sum(1 for lead in leads if lead.status == LeadStatus.CLOSED_WON)
        lost = sum(1 for lead in leads if lead.status == LeadStatus.CLOSED_LOST)

        rates = {
            "lead_to_qualified": round(100 * reached_qualified / total, 1) if total else None,
            "qualified_to_proposal": round(100 * reached_proposal / reached_qualified, 1) if reached_qualified else None,
            "proposal_to_won": round(100 * won / reached_proposal, 1) if reached_proposal else None,
            "overall_win_rate": round(100 * won / (won + lost), 1) if (won + lost) else None,
        }

        return {"period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}, "rates": rates}

    except Exception as e:
        logger.error(f"Failed to get conversion rates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rep-performance")
async def get_rep_performance(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Real sales rep leaderboard - won deals grouped by Lead.assigned_rep"""
    try:
        query = (
            select(Lead.assigned_rep, func.count(Deal.id), func.sum(Deal.amount))
            .join(Deal, Deal.lead_id == Lead.id)
            .where(Deal.is_won == True)  # noqa: E712
            .group_by(Lead.assigned_rep)
            .order_by(func.sum(Deal.amount).desc())
            .limit(limit)
        )
        result = await db.execute(query)
        rows = result.all()

        reps = [
            {"rep": rep or "Unassigned", "deals_won": count, "revenue": revenue or 0}
            for rep, count, revenue in rows
        ]

        return {"total": len(reps), "reps": reps}

    except Exception as e:
        logger.error(f"Failed to get rep performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))
