"""
Tests for the new agent + voice endpoints.

These are deliberately offline — they exercise the fixture-fallback paths so
CI runs deterministically. The live Claude path is exercised by the manual
integration smoke-tests in /backend/.test_data/.
"""

import pytest

from app.config import Settings, get_settings


def test_voice_intake_offline_falls_back_to_fixture(client, monkeypatch):
    # Force fixture mode regardless of hardcoded key
    monkeypatch.setattr(
        "app.services.ai_receipt_extractor.get_settings",
        lambda: Settings(ANTHROPIC_API_KEY=None),
    )
    response = client.post(
        "/api/receipts/voice",
        json={"transcript": "I had a burger and fries at Burger King for ten euros"},
    )
    assert response.status_code == 200
    receipt = response.json()
    assert receipt["status"] == "READY"
    assert receipt["items"], "voice intake should produce line items"
    # Fast-food keywords route to the BK fixture
    assert receipt["merchant_name"] == "Burger King"


def test_voice_intake_rejects_empty_transcript(client):
    response = client.post("/api/receipts/voice", json={"transcript": ""})
    assert response.status_code == 400


def test_agent_advise_falls_back_when_no_key_and_returns_plan(client, monkeypatch):
    # Force fallback by stripping the API key from the settings the agent uses.
    monkeypatch.setattr(
        "app.services.ai_agent.get_settings",
        lambda: Settings(ANTHROPIC_API_KEY=None),
    )
    response = client.post("/api/agent/advise")
    assert response.status_code == 200
    plan = response.json()
    assert plan["fallback"] is True, "with no key the agent must take the deterministic path"
    for required in ("summary", "headline_number", "tip", "risk_level", "swaps", "actions"):
        assert required in plan, f"missing key: {required}"


def test_confirm_action_demo_safe_path_records_transaction(client):
    response = client.post(
        "/api/agent/confirm-action",
        json={
            "kind": "savings_transfer",
            "payload": {"amount_eur": 15.0, "rationale": "Test commitment savings"},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["executed"] == "demo"
    assert body["amount_eur"] == 15.0


def test_confirm_action_rejects_unknown_kinds(client):
    response = client.post(
        "/api/agent/confirm-action",
        json={"kind": "wire_to_offshore", "payload": {"amount_eur": 1000}},
    )
    assert response.status_code == 400


def test_confirm_action_rejects_out_of_bounds_amount(client):
    response = client.post(
        "/api/agent/confirm-action",
        json={"kind": "savings_transfer", "payload": {"amount_eur": 999, "rationale": "x"}},
    )
    assert response.status_code == 400
