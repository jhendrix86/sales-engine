"""
Real tests for the SQLAlchemy models - previously completely untested
(only a smoke-import test existed for this engine, unlike the other 3
engines made real this session which already had model-layer coverage).
"""

from sqlalchemy import select

from app.models.activity import Activity, ActivityType
from app.models.crm import CRMContact, CRMIntegration, CRMSyncStatus, CRMType
from app.models.lead import Lead, LeadSource, LeadStatus
from app.models.pipeline import Deal, PipelineStage
from app.models.proposal import Proposal, ProposalStatus


async def test_lead_defaults(db_session):
    lead = Lead(name="John Doe", email="john@example.com")
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)

    assert lead.status == LeadStatus.NEW
    assert lead.assigned_rep is None


async def test_lead_activity_relationship_round_trips(db_session):
    lead = Lead(name="John Doe", email="john@example.com")
    db_session.add(lead)
    await db_session.flush()

    activity = Activity(lead_id=lead.id, activity_type=ActivityType.CALL, subject="Intro call")
    db_session.add(activity)
    await db_session.commit()

    result = await db_session.execute(select(Lead).where(Lead.id == lead.id))
    fetched = result.scalar_one()
    await db_session.refresh(fetched, attribute_names=["activities"])
    assert len(fetched.activities) == 1


async def test_lead_proposal_relationship_round_trips(db_session):
    lead = Lead(name="John Doe", email="john@example.com")
    db_session.add(lead)
    await db_session.flush()

    proposal = Proposal(lead_id=lead.id, title="Renewal", amount=25000)
    db_session.add(proposal)
    await db_session.commit()

    result = await db_session.execute(select(Lead).where(Lead.id == lead.id))
    fetched = result.scalar_one()
    await db_session.refresh(fetched, attribute_names=["proposals"])
    assert len(fetched.proposals) == 1
    assert fetched.proposals[0].status == ProposalStatus.DRAFT


async def test_deal_requires_a_lead(db_session):
    from sqlalchemy.exc import IntegrityError
    import uuid

    db_session.add(Deal(lead_id=uuid.uuid4(), name="Dangling deal", amount=1000))
    try:
        await db_session.commit()
        assert False, "expected an IntegrityError for a dangling lead_id"
    except IntegrityError:
        await db_session.rollback()


async def test_pipeline_stage_is_unique_by_name(db_session):
    from sqlalchemy.exc import IntegrityError

    db_session.add(PipelineStage(name="New", order=1))
    await db_session.commit()

    db_session.add(PipelineStage(name="New", order=2))
    try:
        await db_session.commit()
        assert False, "expected an IntegrityError for a duplicate stage name"
    except IntegrityError:
        await db_session.rollback()


async def test_crm_integration_defaults(db_session):
    integration = CRMIntegration(crm_type=CRMType.HUBSPOT, crm_name="Acme HubSpot")
    db_session.add(integration)
    await db_session.commit()
    await db_session.refresh(integration)

    assert integration.sync_status == CRMSyncStatus.ACTIVE


async def test_crm_contact_requires_lead_and_integration(db_session):
    lead = Lead(name="John Doe", email="john@example.com")
    db_session.add(lead)
    integration = CRMIntegration(crm_type=CRMType.HUBSPOT, crm_name="Acme HubSpot")
    db_session.add(integration)
    await db_session.flush()

    contact = CRMContact(lead_id=lead.id, crm_integration_id=integration.id, crm_contact_id="12345")
    db_session.add(contact)
    await db_session.commit()
    await db_session.refresh(contact)

    assert contact.sync_status.value == "synced"
