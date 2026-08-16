"""
Verifies tenant isolation for sales-engine endpoints.
Tests that automatic query filtering actually isolates data between tenants.
"""

# Use fixed UUIDs that match what we create in conftest
TENANT_A = "3e2a7c54-a950-48f3-9eb9-d1eb6b2d1be2"
TENANT_B = "00000000-0000-0000-0000-000000000001"


async def _create_lead(client, tenant_id, name):
    resp = await client.post(
        "/leads/",
        json={
            "name": name,
            "email": f"{name.lower().replace(' ', '.')}@example.com",
            "company": "Test Company",
            "estimated_value": 10000
        },
        headers={"X-Tenant-ID": tenant_id},
    )
    assert resp.status_code == 200
    return resp.json()["id"]


async def test_tenant_cannot_read_another_tenants_lead(client):
    lead_id = await _create_lead(client, TENANT_A, "John Doe")

    same_tenant = await client.get(f"/leads/{lead_id}", headers={"X-Tenant-ID": TENANT_A})
    assert same_tenant.status_code == 200

    other_tenant = await client.get(f"/leads/{lead_id}", headers={"X-Tenant-ID": TENANT_B})
    assert other_tenant.status_code == 404


async def test_list_leads_is_scoped_per_tenant(client):
    await _create_lead(client, TENANT_A, "Alice Smith")
    await _create_lead(client, TENANT_A, "Bob Johnson")
    await _create_lead(client, TENANT_B, "Charlie Brown")

    a_listing = await client.get("/leads/", headers={"X-Tenant-ID": TENANT_A})
    assert a_listing.status_code == 200
    assert a_listing.json()["total"] == 2

    b_listing = await client.get("/leads/", headers={"X-Tenant-ID": TENANT_B})
    assert b_listing.status_code == 200
    assert b_listing.json()["total"] == 1


async def test_no_tenant_header_sees_everything(client):
    """Fail-open posture: no X-Tenant-ID means no filtering is applied."""
    await _create_lead(client, TENANT_A, "Alice Smith")
    await _create_lead(client, TENANT_B, "Bob Johnson")

    unscoped = await client.get("/leads/")
    assert unscoped.status_code == 200
    assert unscoped.json()["total"] == 2


async def test_tenant_cannot_modify_another_tenants_lead(client):
    lead_id = await _create_lead(client, TENANT_A, "John Doe")

    # Try to convert as tenant B
    convert_response = await client.post(
        f"/leads/{lead_id}/convert",
        json={"deal_name": "Converted Deal"},
        headers={"X-Tenant-ID": TENANT_B}
    )
    assert convert_response.status_code == 404


async def test_deal_creation_respects_tenant_scoping(client):
    """Deal creation should be tenant-scoped."""
    lead_id = await _create_lead(client, TENANT_A, "Test Lead")

    # Convert to deal for tenant A
    deal_resp = await client.post(
        f"/leads/{lead_id}/convert",
        json={"deal_name": "Test Deal"},
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert deal_resp.status_code == 200
    deal_id = deal_resp.json()["deal_id"]

    # Tenant A can see the deal
    a_deal = await client.get(f"/pipeline/deals/{deal_id}", headers={"X-Tenant-ID": TENANT_A})
    assert a_deal.status_code == 200

    # Tenant B cannot see the deal
    b_deal = await client.get(f"/pipeline/deals/{deal_id}", headers={"X-Tenant-ID": TENANT_B})
    assert b_deal.status_code == 404


async def test_crm_integration_respects_tenant_scoping(client):
    """CRM integrations should be tenant-scoped."""
    # Create CRM integration for tenant A
    crm_resp = await client.post(
        "/crm/sync",
        json={
            "crm_type": "hubspot",
            "api_key": "test-key",
            "api_url": "https://api.hubapi.com"
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert crm_resp.status_code == 200
    integration_id = crm_resp.json()["id"]

    # Tenant A can see the integration
    a_integration = await client.get(f"/crm/{integration_id}", headers={"X-Tenant-ID": TENANT_A})
    assert a_integration.status_code == 200

    # Tenant B cannot see the integration
    b_integration = await client.get(f"/crm/{integration_id}", headers={"X-Tenant-ID": TENANT_B})
    assert b_integration.status_code == 404
