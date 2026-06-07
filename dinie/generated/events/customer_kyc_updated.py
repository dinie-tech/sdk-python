# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from ..types import KycRequirement, WebhookEventBase, deserialize_kyc_requirement
from ..types.ids import CustomerId


@dataclass(frozen=True, slots=True)
class CustomerKycUpdatedData:
    external_id: str
    id: CustomerId
    kyc: list[KycRequirement]
    status: Literal["pending_kyc", "under_review", "active"]

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> CustomerKycUpdatedData:
        return cls(
            external_id=raw["external_id"],
            id=raw["id"],
            kyc=[deserialize_kyc_requirement(x) for x in raw["kyc"]],
            status=raw["status"],
        )


@dataclass(frozen=True, slots=True)
class CustomerKycUpdated(WebhookEventBase):
    data: CustomerKycUpdatedData = None  # type: ignore[assignment]

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> CustomerKycUpdated:
        return cls(
            api_version=raw["api_version"],
            created_at=raw["created_at"],
            delivery_id=raw["delivery_id"],
            id=raw["id"],
            timestamp=raw["timestamp"],
            type=raw.get("type", "customer.kyc_updated"),
            data=CustomerKycUpdatedData.deserialize(raw.get("data", {})),
        )


__all__ = ["CustomerKycUpdated", "CustomerKycUpdatedData"]
