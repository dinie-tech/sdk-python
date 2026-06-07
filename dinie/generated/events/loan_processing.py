# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from ..types import WebhookEventBase
from ..types.ids import CreditOfferId, CustomerId, LoanId


@dataclass(frozen=True, slots=True)
class LoanProcessingData:
    ccb_number: str
    credit_offer_id: CreditOfferId
    customer_id: CustomerId
    disbursement_method: str
    id: LoanId
    status: Literal["processing"]

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> LoanProcessingData:
        return cls(
            ccb_number=raw["ccb_number"],
            credit_offer_id=raw["credit_offer_id"],
            customer_id=raw["customer_id"],
            disbursement_method=raw["disbursement_method"],
            id=raw["id"],
            status=raw["status"],
        )


@dataclass(frozen=True, slots=True)
class LoanProcessing(WebhookEventBase):
    data: LoanProcessingData = None  # type: ignore[assignment]

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> LoanProcessing:
        return cls(
            api_version=raw["api_version"],
            created_at=raw["created_at"],
            delivery_id=raw["delivery_id"],
            id=raw["id"],
            timestamp=raw["timestamp"],
            type=raw.get("type", "loan.processing"),
            data=LoanProcessingData.deserialize(raw.get("data", {})),
        )


__all__ = ["LoanProcessing", "LoanProcessingData"]
