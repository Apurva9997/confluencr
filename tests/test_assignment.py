"""The four cases from the assessment, plus the failure paths under reliability.

These call the HTTP API. They fail until acceptance, lookup, and the background
finish step are wired.
"""

import time

from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import WEBHOOK


def test_health(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "HEALTHY"
    assert body["current_time"].endswith("Z")


def test_single_transaction_is_processed_after_the_delay(client):
    accepted = client.post("/v1/webhooks/transactions", json=WEBHOOK)
    assert accepted.status_code == 202

    row = client.get(f"/v1/transactions/{WEBHOOK['transaction_id']}").json()[0]
    assert row["status"] == "PROCESSED"
    assert row["processed_at"] is not None
    assert row["amount"] == 1500
    assert row["currency"] == "INR"


def test_duplicate_webhook_processes_one_transaction(client):
    for _ in range(3):
        accepted = client.post("/v1/webhooks/transactions", json=WEBHOOK)
        assert accepted.status_code == 202

    found = client.get(f"/v1/transactions/{WEBHOOK['transaction_id']}")
    assert found.status_code == 200
    assert len(found.json()) == 1
    assert found.json()[0]["status"] == "PROCESSED"


def test_webhook_stays_under_500ms_while_other_work_is_in_flight(client):
    for index in range(20):
        body = {**WEBHOOK, "transaction_id": f"txn_load_{index}"}
        client.post("/v1/webhooks/transactions", json=body)

    started = time.perf_counter()
    accepted = client.post(
        "/v1/webhooks/transactions",
        json={**WEBHOOK, "transaction_id": "txn_load_probe"},
    )
    elapsed_ms = (time.perf_counter() - started) * 1000

    assert accepted.status_code == 202
    assert elapsed_ms < 500


def test_invalid_body_is_rejected_and_stores_nothing(client):
    rejected = client.post("/v1/webhooks/transactions", json={"amount": 10})
    assert rejected.status_code == 422
    missing = client.get("/v1/transactions/does-not-exist")
    assert missing.status_code == 404


def test_failed_insert_is_not_acknowledged(client, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("database down")

    monkeypatch.setattr("app.main.Transaction.insert", fail)
    accepted = client.post("/v1/webhooks/transactions", json=WEBHOOK)
    assert accepted.status_code == 503
    assert client.get(f"/v1/transactions/{WEBHOOK['transaction_id']}").status_code == 404


def test_restart_finishes_a_row_left_processing(client):
    from datetime import datetime, timezone

    from app.tables import Status, Transaction

    Transaction(
        transaction_id="txn_left_behind",
        source_account="acc_user_789",
        destination_account="acc_merchant_456",
        amount=10,
        currency="INR",
        status=Status.PROCESSING.value,
        created_at=datetime.now(timezone.utc),
    ).save().run_sync()

    with TestClient(app):
        pass
    row = client.get("/v1/transactions/txn_left_behind").json()[0]
    assert row["status"] == "PROCESSED"
    assert row["processed_at"] is not None
