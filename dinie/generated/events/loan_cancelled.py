# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from ..types import LoanError, WebhookEventBase
from ..types.ids import LoanId


@dataclass(frozen=True, slots=True)
class LoanStatusData:
    id: LoanId
    status: Literal["finished", "cancelled", "error"]
    error: LoanError | None = None

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> LoanStatusData:
        return cls(
            id=raw["id"],
            status=raw["status"],
            error=LoanError.deserialize(raw["error"]) if "error" in raw else None,
        )


@dataclass(frozen=True, slots=True)
class LoanCancelled(WebhookEventBase):
    data: LoanStatusData = None  # type: ignore[assignment]

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> LoanCancelled:
        return cls(
            api_version=raw["api_version"],
            created_at=raw["created_at"],
            delivery_id=raw["delivery_id"],
            id=raw["id"],
            timestamp=raw["timestamp"],
            type=raw.get("type", "loan.cancelled"),
            data=LoanStatusData.deserialize(raw.get("data", {})),
        )


__all__ = ["LoanCancelled", "LoanStatusData"]
