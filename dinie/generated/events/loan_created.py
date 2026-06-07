# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from ..types import WebhookEventBase
from ..types.ids import CreditOfferId, CustomerId, LoanId


@dataclass(frozen=True, slots=True)
class LoanCreatedData:
    credit_offer_id: CreditOfferId
    customer_id: CustomerId
    id: LoanId
    installment_count: int
    requested_amount: float
    signing_url: str
    status: Literal["awaiting_signatures"]

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> LoanCreatedData:
        return cls(
            credit_offer_id=raw["credit_offer_id"],
            customer_id=raw["customer_id"],
            id=raw["id"],
            installment_count=raw["installment_count"],
            requested_amount=raw["requested_amount"],
            signing_url=raw["signing_url"],
            status=raw["status"],
        )


@dataclass(frozen=True, slots=True)
class LoanCreated(WebhookEventBase):
    data: LoanCreatedData = None  # type: ignore[assignment]

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> LoanCreated:
        return cls(
            api_version=raw["api_version"],
            created_at=raw["created_at"],
            delivery_id=raw["delivery_id"],
            id=raw["id"],
            timestamp=raw["timestamp"],
            type=raw.get("type", "loan.created"),
            data=LoanCreatedData.deserialize(raw.get("data", {})),
        )


__all__ = ["LoanCreated", "LoanCreatedData"]
