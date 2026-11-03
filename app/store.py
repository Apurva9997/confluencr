from datetime import datetime
from typing import Protocol

from app.models import TransactionRecord
from app.models import WebhookRequest


class TransactionStore(Protocol):
    def insert_if_new(self, body: WebhookRequest, created_at: datetime) -> bool:
        """Insert as PROCESSING. Return False when transaction_id already exists."""

    def get(self, transaction_id: str) -> TransactionRecord | None:
        """Return the stored row, or None."""

    def mark_processed(self, transaction_id: str, processed_at: datetime) -> None:
        """Set status to PROCESSED. A second call must not create another row."""

    def list_processing(self) -> list[TransactionRecord]:
        """Rows still PROCESSING, used by the startup sweep."""
