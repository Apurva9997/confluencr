from typing import Literal

from pydantic import BaseModel, Field


class WebhookRequest(BaseModel):
    transaction_id: str = Field(examples=["txn_abc123def456"])
    source_account: str = Field(examples=["acc_user_789"])
    destination_account: str = Field(examples=["acc_merchant_456"])
    amount: float = Field(examples=[1500])
    currency: str = Field(examples=["INR"])


class Accepted(BaseModel):
    status: Literal["accepted"] = "accepted"


class Health(BaseModel):
    status: Literal["HEALTHY"]
    current_time: str = Field(examples=["2024-01-15T10:30:00Z"])


class TransactionRecord(BaseModel):
    transaction_id: str
    source_account: str
    destination_account: str
    amount: float
    currency: str
    status: Literal["PROCESSING", "PROCESSED"]
    created_at: str = Field(examples=["2024-01-15T10:30:00Z"])
    processed_at: str | None = None
