"""
Seeds the default pipeline_stages on first boot. This is reference/
config data (a picklist every fresh deployment needs to have SOME
stages to move deals through), not a fabricated live metric - same
category as integration-engine's seeded IntegrationTemplate catalog.
Idempotent: only inserts if the table is empty.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pipeline import PipelineStage

_DEFAULT_STAGES = [
    {"name": "New", "order": 1, "win_probability": 10},
    {"name": "Qualified", "order": 2, "win_probability": 30},
    {"name": "Proposal", "order": 3, "win_probability": 60},
    {"name": "Closed Won", "order": 4, "win_probability": 100},
]


async def seed_default_stages(session: AsyncSession) -> None:
    existing = await session.execute(select(PipelineStage.id).limit(1))
    if existing.scalar_one_or_none() is not None:
        return  # already seeded

    for entry in _DEFAULT_STAGES:
        session.add(PipelineStage(**entry))
    await session.commit()
