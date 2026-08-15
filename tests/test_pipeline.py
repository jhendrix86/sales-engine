"""pipeline.py is now real: stages come from the real seeded catalog, deals hit the deals table."""


async def _create_lead(client, **overrides):
    payload = {"name": "John Doe", "email": "john@example.com"}
    payload.update(overrides)
    r = await client.post("/leads/create", json=payload)
    return r.json()


async def test_list_pipeline_stages_reflects_the_real_seeded_catalog(client):
    r = await client.get("/pipeline/stages")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 4
    assert [s["name"] for s in body["stages"]] == ["New", "Qualified", "Proposal", "Closed Won"]


async def test_create_deal_persists_a_real_row(client):
    lead = await _create_lead(client)

    r = await client.post("/pipeline/deals", json={"lead_id": lead["id"], "name": "Acme Renewal", "amount": 25000})
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Acme Renewal"
    assert body["is_won"] is False
    assert body["id"]  # a real generated UUID, not "deal_123"


async def test_create_deal_for_unknown_lead_is_a_real_404(client):
    r = await client.post("/pipeline/deals", json={"lead_id": "00000000-0000-0000-0000-000000000000", "name": "x", "amount": 100})
    assert r.status_code == 404


async def test_create_deal_with_unknown_stage_is_a_real_404(client):
    lead = await _create_lead(client)
    r = await client.post("/pipeline/deals", json={
        "lead_id": lead["id"], "name": "x", "amount": 100, "stage_id": "00000000-0000-0000-0000-000000000000",
    })
    assert r.status_code == 404


async def test_get_deal_returns_the_real_row(client):
    lead = await _create_lead(client)
    created = (await client.post("/pipeline/deals", json={"lead_id": lead["id"], "name": "x", "amount": 100})).json()

    r = await client.get(f"/pipeline/deals/{created['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


async def test_get_unknown_deal_is_a_real_404(client):
    r = await client.get("/pipeline/deals/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_list_deals_reflects_real_created_rows(client):
    lead = await _create_lead(client)
    await client.post("/pipeline/deals", json={"lead_id": lead["id"], "name": "one", "amount": 100})
    await client.post("/pipeline/deals", json={"lead_id": lead["id"], "name": "two", "amount": 200})

    r = await client.get("/pipeline/deals")
    body = r.json()
    assert body["total"] == 2
    assert {d["name"] for d in body["deals"]} == {"one", "two"}


async def test_move_deal_stage_validates_the_target_stage_for_real(client):
    lead = await _create_lead(client)
    deal = (await client.post("/pipeline/deals", json={"lead_id": lead["id"], "name": "x", "amount": 100})).json()
    stages = (await client.get("/pipeline/stages")).json()["stages"]
    proposal_stage = next(s for s in stages if s["name"] == "Proposal")

    r = await client.post(f"/pipeline/deals/{deal['id']}/move", params={"stage_id": proposal_stage["id"]})
    assert r.status_code == 200
    assert r.json()["stage_id"] == proposal_stage["id"]


async def test_move_deal_to_unknown_stage_is_a_real_404(client):
    lead = await _create_lead(client)
    deal = (await client.post("/pipeline/deals", json={"lead_id": lead["id"], "name": "x", "amount": 100})).json()

    r = await client.post(f"/pipeline/deals/{deal['id']}/move", params={"stage_id": "00000000-0000-0000-0000-000000000000"})
    assert r.status_code == 404


async def test_move_unknown_deal_is_a_real_404(client):
    r = await client.post("/pipeline/deals/00000000-0000-0000-0000-000000000000/move", params={"stage_id": "00000000-0000-0000-0000-000000000000"})
    assert r.status_code == 404
