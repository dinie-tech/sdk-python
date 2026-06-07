# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from ..types import LoanPayment, WebhookEventBase
from ..types.ids import LoanId


@dataclass(frozen=True, slots=True)
class LoanPaymentReceivedData:
    id: LoanId
    payment: LoanPayment
    status: Literal["active"]

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> LoanPaymentReceivedData:
        return cls(
            id=raw["id"],
            payment=LoanPayment.deserialize(raw["payment"]),
            status=raw["status"],
        )


@dataclass(frozen=True, slots=True)
class LoanPaymentReceived(WebhookEventBase):
    data: LoanPaymentReceivedData = None  # type: ignore[assignment]

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> LoanPaymentReceived:
        return cls(
            api_version=raw["api_version"],
            created_at=raw["created_at"],
            delivery_id=raw["delivery_id"],
            id=raw["id"],
            timestamp=raw["timestamp"],
            type=raw.get("type", "loan.payment_received"),
            data=LoanPaymentReceivedData.deserialize(raw.get("data", {})),
        )


__all__ = ["LoanPaymentReceived", "LoanPaymentReceivedData"]
