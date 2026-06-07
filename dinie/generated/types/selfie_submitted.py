# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .enums import ReviewStatus
from .selfie_attachment import SelfieAttachment


@dataclass(frozen=True, slots=True)
class SelfieSubmitted:
    attachments: list[SelfieAttachment]
    evidence_type: Literal["selfie"]
    review_reason: str | None
    review_status: ReviewStatus

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> SelfieSubmitted:
        return cls(
            attachments=[SelfieAttachment.deserialize(x) for x in raw["attachments"]],
            evidence_type=raw["evidence_type"],
            review_reason=raw["review_reason"],
            review_status=raw["review_status"],
        )
