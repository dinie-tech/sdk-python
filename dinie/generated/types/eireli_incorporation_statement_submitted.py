# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .eireli_incorporation_statement_attachment import EireliIncorporationStatementAttachment
from .enums import ReviewStatus


@dataclass(frozen=True, slots=True)
class EireliIncorporationStatementSubmitted:
    attachments: list[EireliIncorporationStatementAttachment]
    evidence_type: Literal["eireli_incorporation_statement"]
    review_reason: str | None
    review_status: ReviewStatus

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> EireliIncorporationStatementSubmitted:
        return cls(
            attachments=[
                EireliIncorporationStatementAttachment.deserialize(x) for x in raw["attachments"]
            ],
            evidence_type=raw["evidence_type"],
            review_reason=raw["review_reason"],
            review_status=raw["review_status"],
        )
