# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .enums import ReviewStatus
from .identity_cnh_attachment import IdentityCnhAttachment


@dataclass(frozen=True, slots=True)
class IdentityCnhSubmitted:
    attachments: list[IdentityCnhAttachment]
    evidence_type: Literal["cnh"]
    review_reason: str | None
    review_status: ReviewStatus

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> IdentityCnhSubmitted:
        return cls(
            attachments=[IdentityCnhAttachment.deserialize(x) for x in raw["attachments"]],
            evidence_type=raw["evidence_type"],
            review_reason=raw["review_reason"],
            review_status=raw["review_status"],
        )
