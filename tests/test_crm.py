"""
crm.py is now real: integrations hit the crm_integrations table, and
/sync attempts a real outbound call to the connected CRM provider
(app/services/crm_client.py, mocked here via respx against each
provider's actual real REST endpoint).
"""

import httpx
import respx


async def _create_integration(client, **overrides):
    payload = {"crm_type": "hubspot", "crm_name": "Acme HubSpot"}
    payload.update(overrides)
    r = await client.post("/crm/integrations", json=payload)
    assert r.status_code == 200
    return r.json()


async def test_create_crm_integration_persists_a_real_row(client):
    body = await _create_integration(client)
    assert body["crm_type"] == "hubspot"
    assert body["sync_status"] == "active"
    assert body["id"]  # a real generated UUID, not "crm_int_123"


async def test_create_crm_integration_rejects_invalid_type(client):
    r = await client.post("/crm/integrations", json={"crm_type": "not_a_real_crm", "crm_name": "x"})
    assert r.status_code == 422


async def test_list_crm_integrations_reflects_real_created_rows(client):
    await _create_integration(client, crm_name="one")
    await _create_integration(client, crm_type="salesforce", crm_name="two")

    r = await client.get("/crm/integrations")
    body = r.json()
    assert body["total"] == 2
    assert {i["crm_name"] for i in body["integrations"]} == {"one", "two"}


async def test_sync_without_api_key_reports_honest_failure(client):
    integration = await _create_integration(client)  # no api_key given

    r = await client.post(f"/crm/integrations/{integration['id']}/sync")
    assert r.status_code == 200
    body = r.json()
    assert body["sync_status"] == "error"
    assert "api_key" in body["error"]
    assert body["contacts_fetched"] == 0


async def test_sync_unknown_integration_is_a_real_404(client):
    r = await client.post("/crm/integrations/00000000-0000-0000-0000-000000000000/sync")
    assert r.status_code == 404


@respx.mock
async def test_sync_hubspot_pulls_real_contacts(client):
    respx.get("https://api.hubapi.com/crm/v3/objects/contacts").mock(
        return_value=httpx.Response(200, json={"results": [{"id": "1"}, {"id": "2"}]})
    )

    integration = await _create_integration(client, api_key="test-key")
    r = await client.post(f"/crm/integrations/{integration['id']}/sync")

    assert r.status_code == 200
    body = r.json()
    assert body["sync_status"] == "active"
    assert body["contacts_fetched"] == 2
    assert body["error"] is None


@respx.mock
async def test_sync_salesforce_requires_instance_url(client):
    integration = await _create_integration(client, crm_type="salesforce", api_key="session-token")
    # no api_url given

    r = await client.post(f"/crm/integrations/{integration['id']}/sync")
    body = r.json()
    assert body["sync_status"] == "error"
    assert "api_url" in body["error"]


@respx.mock
async def test_sync_salesforce_pulls_real_contacts(client):
    respx.get("https://acme.my.salesforce.com/services/data/v58.0/query").mock(
        return_value=httpx.Response(200, json={"records": [{"Id": "003abc"}]})
    )

    integration = await _create_integration(
        client, crm_type="salesforce", crm_name="Acme SF", api_key="session-token", api_url="https://acme.my.salesforce.com",
    )
    r = await client.post(f"/crm/integrations/{integration['id']}/sync")

    body = r.json()
    assert body["sync_status"] == "active"
    assert body["contacts_fetched"] == 1


@respx.mock
async def test_sync_reports_honest_failure_on_provider_error(client):
    respx.get("https://api.hubapi.com/crm/v3/objects/contacts").mock(return_value=httpx.Response(401, text="unauthorized"))

    integration = await _create_integration(client, api_key="bad-key")
    r = await client.post(f"/crm/integrations/{integration['id']}/sync")

    body = r.json()
    assert body["sync_status"] == "error"
    assert "401" in body["error"]


async def test_list_crm_contacts_is_honestly_empty_with_none_synced(client):
    r = await client.get("/crm/contacts")
    assert r.status_code == 200
    assert r.json() == {"total": 0, "contacts": [], "filters": {"lead_id": None}, "pagination": {"limit": 50, "offset": 0}}
