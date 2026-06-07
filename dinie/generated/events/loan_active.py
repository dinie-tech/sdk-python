# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from ..types import WebhookEventBase
from ..types.ids import LoanId


@dataclass(frozen=True, slots=True)
class LoanActiveData:
    id: LoanId
    principal_amount: float
    requested_amount: float
    status: Literal["active"]

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> LoanActiveData:
        return cls(
            id=raw["id"],
            principal_amount=raw["principal_amount"],
            requested_amount=raw["requested_amount"],
            status=raw["status"],
        )


@dataclass(frozen=True, slots=True)
class LoanActive(WebhookEventBase):
    data: LoanActiveData = None  # type: ignore[assignment]

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> LoanActive:
        return cls(
            api_version=raw["api_version"],
            created_at=raw["created_at"],
            delivery_id=raw["delivery_id"],
            id=raw["id"],
            timestamp=raw["timestamp"],
            type=raw.get("type", "loan.active"),
            data=LoanActiveData.deserialize(raw.get("data", {})),
        )


__all__ = ["LoanActive", "LoanActiveData"]
