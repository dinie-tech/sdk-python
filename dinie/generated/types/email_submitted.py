# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .email_attachment import EmailAttachment
from .enums import ReviewStatus


@dataclass(frozen=True, slots=True)
class EmailSubmitted:
    attachments: list[EmailAttachment]
    evidence_type: Literal["email"]
    review_reason: str | None
    review_status: ReviewStatus

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> EmailSubmitted:
        return cls(
            attachments=[EmailAttachment.deserialize(x) for x in raw["attachments"]],
            evidence_type=raw["evidence_type"],
            review_reason=raw["review_reason"],
            review_status=raw["review_status"],
        )
