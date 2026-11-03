import asyncio
from datetime import datetime, timezone

from app.tables import Status, Transaction


async def process_transaction(transaction_id: str, delay_seconds: float) -> None:
    """Wait, then mark the stored row PROCESSED. Runs after the 202 is sent."""
    await asyncio.sleep(delay_seconds)
    await Transaction.update(
        {
            Transaction.status: Status.PROCESSED.value,
            Transaction.processed_at: datetime.now(timezone.utc),
        }
    ).where(Transaction.transaction_id == transaction_id)


async def resume_processing(delay_seconds: float) -> None:
    """Finish rows left PROCESSING by a process that died during the wait."""
    rows = await Transaction.select(Transaction.transaction_id).where(
        Transaction.status == Status.PROCESSING.value
    )
    await asyncio.gather(
        *(process_transaction(row["transaction_id"], delay_seconds) for row in rows)
    )
