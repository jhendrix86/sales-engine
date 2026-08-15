"""
proposals.py is now real: every endpoint reads/writes the proposals
table, and /send attempts a real delivery via notification-engine's
real /notifications/send (mocked here via respx).
"""

import httpx
import respx


async def _create_lead(client, **overrides):
    payload = {"name": "John Doe", "email": "john@example.com"}
    payload.update(overrides)
    r = await client.post("/leads/create", json=payload)
    return r.json()


async def _create_proposal(client, lead_id, **overrides):
    payload = {"lead_id": lead_id, "title": "Acme Renewal", "amount": 25000}
    payload.update(overrides)
    r = await client.post("/proposals/", json=payload)
    assert r.status_code == 200
    return r.json()


async def test_create_proposal_persists_a_real_row(client):
    lead = await _create_lead(client)
    body = await _create_proposal(client, lead["id"])

    assert body["title"] == "Acme Renewal"
    assert body["status"] == "draft"
    assert body["id"]  # a real generated UUID, not "proposal_123"


async def test_create_proposal_for_unknown_lead_is_a_real_404(client):
    r = await client.post("/proposals/", json={"lead_id": "00000000-0000-0000-0000-000000000000", "title": "x", "amount": 100})
    assert r.status_code == 404


async def test_send_proposal_without_notification_engine_reachable_reports_honest_failure(client):
    lead = await _create_lead(client)
    proposal = await _create_proposal(client, lead["id"])

    r = await client.post(f"/proposals/{proposal['id']}/send")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "draft"  # never transitioned - delivery genuinely failed
    assert body["delivery_error"] is not None


async def test_send_unknown_proposal_is_a_real_404(client):
    r = await client.post("/proposals/00000000-0000-0000-0000-000000000000/send")
    assert r.status_code == 404


@respx.mock
async def test_send_proposal_delivers_for_real_via_notification_engine(client):
    respx.post("http://localhost:8037/notifications/send").mock(
        return_value=httpx.Response(200, json={"status": "sent"})
    )

    lead = await _create_lead(client, email="lead@example.com")
    proposal = await _create_proposal(client, lead["id"])

    r = await client.post(f"/proposals/{proposal['id']}/send")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "sent"
    assert body["sent_at"] is not None
    assert body["delivery_error"] is None


@respx.mock
async def test_send_proposal_reports_honest_failure_when_notification_engine_rejects_it(client):
    respx.post("http://localhost:8037/notifications/send").mock(
        return_value=httpx.Response(200, json={"status": "failed", "error_message": "SendGrid is not configured"})
    )

    lead = await _create_lead(client)
    proposal = await _create_proposal(client, lead["id"])

    r = await client.post(f"/proposals/{proposal['id']}/send")
    body = r.json()
    assert body["status"] == "draft"
    assert "SendGrid" in body["delivery_error"]


async def test_get_proposal_returns_the_real_row(client):
    lead = await _create_lead(client)
    proposal = await _create_proposal(client, lead["id"])

    r = await client.get(f"/proposals/{proposal['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == proposal["id"]


async def test_get_unknown_proposal_is_a_real_404(client):
    r = await client.get("/proposals/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_list_proposals_filters_by_lead_id_for_real(client):
    lead_a = await _create_lead(client, email="a@example.com")
    lead_b = await _create_lead(client, email="b@example.com")
    await _create_proposal(client, lead_a["id"], title="for-a")
    await _create_proposal(client, lead_b["id"], title="for-b")

    r = await client.get("/proposals/", params={"lead_id": lead_a["id"]})
    body = r.json()
    assert body["total"] == 1
    assert body["proposals"][0]["title"] == "for-a"
