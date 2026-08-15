"""
analytics.py is now real: every endpoint computes from actual leads/
deals in the database instead of returning fixed literals.
"""


async def _create_lead(client, **overrides):
    payload = {"name": "John Doe", "email": "john@example.com"}
    payload.update(overrides)
    return (await client.post("/leads/create", json=payload)).json()


async def _create_deal(client, lead_id, **overrides):
    payload = {"lead_id": lead_id, "name": "Deal", "amount": 1000}
    payload.update(overrides)
    return (await client.post("/pipeline/deals", json=payload)).json()


async def test_pipeline_summary_with_no_deals_is_honestly_empty(client):
    r = await client.get("/analytics/pipeline-summary")
    assert r.status_code == 200
    summary = r.json()["summary"]
    assert summary["total_deals"] == 0
    assert summary["total_value"] == 0
    assert summary["by_stage"] == []


async def test_pipeline_summary_aggregates_real_deals(client):
    lead = await _create_lead(client)
    stages = (await client.get("/pipeline/stages")).json()["stages"]
    proposal_stage = next(s for s in stages if s["name"] == "Proposal")

    await _create_deal(client, lead["id"], amount=100, stage_id=proposal_stage["id"])
    await _create_deal(client, lead["id"], amount=200, stage_id=proposal_stage["id"])

    r = await client.get("/analytics/pipeline-summary")
    summary = r.json()["summary"]
    assert summary["total_deals"] == 2
    assert summary["total_value"] == 300
    assert summary["by_stage"] == [{"stage": "Proposal", "count": 2, "value": 300}]


async def test_pipeline_summary_excludes_lost_deals(client, db_session):
    from app.models.pipeline import Deal
    import uuid

    lead = await _create_lead(client)
    won_deal = await _create_deal(client, lead["id"], amount=500)

    # Mark a second deal lost directly (no "lose" endpoint exists yet - real DB state check)
    lost = Deal(lead_id=uuid.UUID(lead["id"]), name="Lost Deal", amount=999, is_lost=True)
    db_session.add(lost)
    await db_session.commit()

    r = await client.get("/analytics/pipeline-summary")
    summary = r.json()["summary"]
    assert summary["total_deals"] == 1
    assert summary["total_value"] == 500


async def test_conversion_rates_with_no_leads_reports_null_not_a_fabricated_percentage(client):
    r = await client.get("/analytics/conversion-rates")
    rates = r.json()["rates"]
    assert rates["lead_to_qualified"] is None
    assert rates["overall_win_rate"] is None


async def test_conversion_rates_computes_real_percentages(client):
    a = await _create_lead(client, email="a@example.com")
    await _create_lead(client, email="b@example.com")  # stays "new"
    await client.post(f"/leads/{a['id']}/convert")  # a -> qualified

    r = await client.get("/analytics/conversion-rates")
    rates = r.json()["rates"]
    assert rates["lead_to_qualified"] == 50.0


async def test_rep_performance_with_no_won_deals_is_honestly_empty(client):
    r = await client.get("/analytics/rep-performance")
    assert r.status_code == 200
    assert r.json() == {"total": 0, "reps": []}


async def test_rep_performance_aggregates_real_won_deals(client, db_session):
    from app.models.pipeline import Deal
    import uuid

    lead = await _create_lead(client, assigned_rep="Alex Rivera")
    db_session.add(Deal(lead_id=uuid.UUID(lead["id"]), name="Won Deal", amount=5000, is_won=True))
    await db_session.commit()

    r = await client.get("/analytics/rep-performance")
    body = r.json()
    assert body["total"] == 1
    assert body["reps"][0]["rep"] == "Alex Rivera"
    assert body["reps"][0]["revenue"] == 5000
    assert body["reps"][0]["deals_won"] == 1
