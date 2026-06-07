# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .enums import ReviewStatus
from .identity_rg_attachment import IdentityRgAttachment


@dataclass(frozen=True, slots=True)
class IdentityRgSubmitted:
    attachments: list[IdentityRgAttachment]
    evidence_type: Literal["rg"]
    review_reason: str | None
    review_status: ReviewStatus

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> IdentityRgSubmitted:
        return cls(
            attachments=[IdentityRgAttachment.deserialize(x) for x in raw["attachments"]],
            evidence_type=raw["evidence_type"],
            review_reason=raw["review_reason"],
            review_status=raw["review_status"],
        )
