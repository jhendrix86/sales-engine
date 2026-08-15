"""leads.py is now real: every endpoint reads/writes the leads table."""


async def _create_lead(client, **overrides):
    payload = {"name": "John Doe", "email": "john@example.com", "company": "Acme Corp", "estimated_value": 10000}
    payload.update(overrides)
    r = await client.post("/leads/create", json=payload)
    assert r.status_code == 200
    return r.json()


async def test_create_lead_persists_a_real_row(client):
    body = await _create_lead(client)
    assert body["name"] == "John Doe"
    assert body["status"] == "new"
    assert body["id"]  # a real generated UUID, not "lead_123"


async def test_create_lead_requires_declared_fields(client):
    r = await client.post("/leads/create", json={"name": "x"})
    assert r.status_code == 422


async def test_create_lead_rejects_invalid_source(client):
    r = await client.post("/leads/create", json={"name": "x", "email": "x@example.com", "source": "cold_call"})
    assert r.status_code == 422


async def test_convert_lead_creates_a_real_deal(client):
    lead = await _create_lead(client)

    r = await client.post(f"/leads/{lead['id']}/convert")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "qualified"
    assert body["deal_id"]

    deal = (await client.get(f"/pipeline/deals/{body['deal_id']}")).json()
    assert deal["lead_id"] == lead["id"]
    assert deal["amount"] == 10000


async def test_convert_unknown_lead_is_a_real_404(client):
    r = await client.post("/leads/00000000-0000-0000-0000-000000000000/convert")
    assert r.status_code == 404


async def test_get_lead_returns_the_real_row(client):
    lead = await _create_lead(client)
    r = await client.get(f"/leads/{lead['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == lead["id"]


async def test_get_unknown_lead_is_a_real_404(client):
    r = await client.get("/leads/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_list_leads_reflects_real_created_rows(client):
    await _create_lead(client, name="one", email="one@example.com")
    await _create_lead(client, name="two", email="two@example.com")

    r = await client.get("/leads/")
    body = r.json()
    assert body["total"] == 2
    assert {l["name"] for l in body["leads"]} == {"one", "two"}


async def test_list_leads_filters_by_status_for_real(client):
    lead = await _create_lead(client, name="converted")
    await client.post(f"/leads/{lead['id']}/convert")
    await _create_lead(client, name="still-new")

    r = await client.get("/leads/", params={"status": "qualified"})
    body = r.json()
    assert body["total"] == 1
    assert body["leads"][0]["name"] == "converted"
