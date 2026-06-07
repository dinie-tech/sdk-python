# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from ..types import LoanSigner, WebhookEventBase
from ..types.ids import LoanId


@dataclass(frozen=True, slots=True)
class LoanSignatureReceivedData:
    id: LoanId
    signatures_received: int
    signatures_required: int
    signer: LoanSigner
    status: Literal["awaiting_signatures"]

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> LoanSignatureReceivedData:
        return cls(
            id=raw["id"],
            signatures_received=raw["signatures_received"],
            signatures_required=raw["signatures_required"],
            signer=LoanSigner.deserialize(raw["signer"]),
            status=raw["status"],
        )


@dataclass(frozen=True, slots=True)
class LoanSignatureReceived(WebhookEventBase):
    data: LoanSignatureReceivedData = None  # type: ignore[assignment]

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> LoanSignatureReceived:
        return cls(
            api_version=raw["api_version"],
            created_at=raw["created_at"],
            delivery_id=raw["delivery_id"],
            id=raw["id"],
            timestamp=raw["timestamp"],
            type=raw.get("type", "loan.signature_received"),
            data=LoanSignatureReceivedData.deserialize(raw.get("data", {})),
        )


__all__ = ["LoanSignatureReceived", "LoanSignatureReceivedData"]
