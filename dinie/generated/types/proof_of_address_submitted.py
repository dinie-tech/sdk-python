# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .enums import ReviewStatus
from .proof_of_address_attachment import ProofOfAddressAttachment


@dataclass(frozen=True, slots=True)
class ProofOfAddressSubmitted:
    attachments: list[ProofOfAddressAttachment]
    evidence_type: Literal["proof_of_address"]
    review_reason: str | None
    review_status: ReviewStatus

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> ProofOfAddressSubmitted:
        return cls(
            attachments=[ProofOfAddressAttachment.deserialize(x) for x in raw["attachments"]],
            evidence_type=raw["evidence_type"],
            review_reason=raw["review_reason"],
            review_status=raw["review_status"],
        )
