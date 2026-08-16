"""
Verifies tenant context assignment for sales-engine endpoints.
Tests that apply_tenant_context() correctly assigns tenant_id on create.
Note: Automatic query filtering is not yet implemented - this test validates
create-time tenant assignment only.
"""

# Use fixed UUIDs that match what we create in conftest
TENANT_A = "3e2a7c54-a950-48f3-9eb9-d1eb6b2d1be2"
TENANT_B = "00000000-0000-0000-0000-000000000001"


async def test_apply_tenant_context_on_lead_create(client, db_session):
    """Verify that apply_tenant_context assigns tenant_id on lead creation."""
    from app.models.lead import Lead
    import uuid
    
    # Create lead for tenant A
    result = await client.post(
        "/leads/",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "company": "Test Company",
            "estimated_value": 10000
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert result.status_code == 200
    lead_id = result.json()["id"]
    
    # Verify tenant_id was correctly assigned
    lead = await db_session.get(Lead, uuid.UUID(lead_id))
    assert lead is not None
    assert str(lead.tenant_id) == TENANT_A


async def test_apply_tenant_context_on_deal_create(client, db_session):
    """Verify that apply_tenant_context assigns tenant_id on deal creation."""
    from app.models.pipeline import Deal
    import uuid
    
    # Create lead for tenant A
    lead_result = await client.post(
        "/leads/",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "company": "Test Company",
            "estimated_value": 10000
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert lead_result.status_code == 200
    lead_id = lead_result.json()["id"]
    
    # Convert to deal for tenant A
    deal_result = await client.post(
        f"/leads/{lead_id}/convert",
        json={"deal_name": "Test Deal"},
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert deal_result.status_code == 200
    deal_id = deal_result.json()["deal_id"]
    
    # Verify deal tenant_id was correctly assigned
    deal = await db_session.get(Deal, uuid.UUID(deal_id))
    assert deal is not None
    assert str(deal.tenant_id) == TENANT_A


async def test_apply_tenant_context_on_crm_integration_create(client, db_session):
    """Verify that apply_tenant_context assigns tenant_id on CRM integration creation."""
    from app.models.crm import CRMIntegration
    import uuid
    
    # Create CRM integration for tenant A
    result = await client.post(
        "/crm/sync",
        json={
            "crm_type": "hubspot",
            "api_key": "test-key",
            "api_url": "https://api.hubapi.com"
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert result.status_code == 200
    integration_id = result.json()["id"]
    
    # Verify integration tenant_id was correctly assigned
    integration = await db_session.get(CRMIntegration, uuid.UUID(integration_id))
    assert integration is not None
    assert str(integration.tenant_id) == TENANT_A


async def test_apply_tenant_context_on_proposal_create(client, db_session):
    """Verify that apply_tenant_context assigns tenant_id on proposal creation."""
    from app.models.proposal import Proposal
    import uuid
    
    # Create lead for tenant A
    lead_result = await client.post(
        "/leads/",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "company": "Test Company",
            "estimated_value": 10000
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert lead_result.status_code == 200
    lead_id = lead_result.json()["id"]
    
    # Create proposal for tenant A
    proposal_result = await client.post(
        f"/proposals/create/{lead_id}",
        json={
            "title": "Test Proposal",
            "amount": 5000,
            "valid_until": "2026-12-31"
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert proposal_result.status_code == 200
    proposal_id = proposal_result.json()["id"]
    
    # Verify proposal tenant_id was correctly assigned
    proposal = await db_session.get(Proposal, uuid.UUID(proposal_id))
    assert proposal is not None
    assert str(proposal.tenant_id) == TENANT_A
