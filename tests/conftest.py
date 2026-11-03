import os

import pytest
from fastapi.testclient import TestClient
from piccolo.engine.sqlite import SQLiteEngine

os.environ["PROCESS_DELAY_SECONDS"] = "0"

from app.main import app  # noqa: E402
from app.tables import Transaction  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = SQLiteEngine(path=str(tmp_path / "test.sqlite"))
    monkeypatch.setattr(Transaction._meta, "db", engine)
    Transaction.create_table(if_not_exists=True).run_sync()
    with TestClient(app) as test_client:
        yield test_client


WEBHOOK = {
    "transaction_id": "txn_abc123def456",
    "source_account": "acc_user_789",
    "destination_account": "acc_merchant_456",
    "amount": 1500,
    "currency": "INR",
}
