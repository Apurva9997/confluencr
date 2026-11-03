import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import BackgroundTasks, FastAPI, HTTPException

from app.config import get_settings
from app.models import Accepted, Health, TransactionRecord, WebhookRequest
from app.processing import process_transaction, resume_processing
from app.tables import Status, Transaction

settings = get_settings()
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # One pool, kept under the Supabase session pooler's 15-client cap.
    # Without it every request opens its own connection and a burst is rejected.
    # Use the table's engine: tests point that at SQLite, which has no pool.
    engine = Transaction._meta.db
    if engine.engine_type == "postgres":
        await engine.start_connection_pool(min_size=1, max_size=8)
    try:
        await resume_processing(settings.process_delay_seconds)
    except Exception:
        log.exception("startup sweep failed; the next start will retry it")
    yield
    if engine.engine_type == "postgres" and engine.pool:
        await engine.close_connection_pool()


app = FastAPI(
    title="Transaction webhook service",
    description="Accepts a payment webhook, returns 202, and finishes the transaction in the background.",
    version="0.1.0",
    lifespan=lifespan,
)


def utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def as_record(row: dict) -> dict:
    record = dict(row)
    record["amount"] = float(record["amount"])
    for key in ("created_at", "processed_at"):
        value = record[key]
        if isinstance(value, datetime):
            record[key] = value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return record


@app.get("/", response_model=Health)
def health() -> Health:
    return Health(status="HEALTHY", current_time=utc_now_z())


@app.post(
    "/v1/webhooks/transactions",
    status_code=202,
    response_model=Accepted,
    responses={503: {"description": "The transaction was not stored"}},
)
async def accept_webhook(body: WebhookRequest, background: BackgroundTasks) -> Accepted:
    try:
        inserted = (
            await Transaction.insert(
                Transaction(
                    transaction_id=body.transaction_id,
                    source_account=body.source_account,
                    destination_account=body.destination_account,
                    amount=body.amount,
                    currency=body.currency,
                    status=Status.PROCESSING.value,
                    created_at=datetime.now(timezone.utc),
                )
            )
            .on_conflict(Transaction.transaction_id, action="DO NOTHING")
            .returning(Transaction.transaction_id)
            .run()
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="transaction was not stored") from exc

    if inserted:
        background.add_task(
            process_transaction,
            body.transaction_id,
            settings.process_delay_seconds,
        )
    return Accepted()


@app.get(
    "/v1/transactions/{transaction_id}",
    response_model=list[TransactionRecord],
    responses={404: {"description": "No transaction with this id"}},
)
async def get_transaction(transaction_id: str) -> list[TransactionRecord]:
    rows = await Transaction.select().where(Transaction.transaction_id == transaction_id)
    if not rows:
        raise HTTPException(status_code=404, detail="transaction not found")
    return [TransactionRecord(**as_record(row)) for row in rows]
