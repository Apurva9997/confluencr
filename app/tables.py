from enum import Enum

from piccolo.columns import Numeric, Text, Timestamptz
from piccolo.columns.defaults.timestamptz import TimestamptzNow
from piccolo.table import Table


class Status(Enum):
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"


class Transaction(Table, tablename="transactions"):
    """One payment webhook. transaction_id is the idempotency key."""

    transaction_id = Text(primary_key=True)
    source_account = Text(null=False)
    destination_account = Text(null=False)
    amount = Numeric(digits=(18, 2), null=False)
    currency = Text(null=False)
    status = Text(null=False, choices=Status, default=Status.PROCESSING)
    created_at = Timestamptz(null=False, default=TimestamptzNow())
    processed_at = Timestamptz(null=True, default=None)
