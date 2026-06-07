# generated — do not edit
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .enums import ReviewStatus
from .income_statement_attachment import IncomeStatementAttachment


@dataclass(frozen=True, slots=True)
class IncomeStatementSubmitted:
    attachments: list[IncomeStatementAttachment]
    evidence_type: Literal["income_statement"]
    review_reason: str | None
    review_status: ReviewStatus

    @classmethod
    def deserialize(cls, raw: dict[str, Any]) -> IncomeStatementSubmitted:
        return cls(
            attachments=[IncomeStatementAttachment.deserialize(x) for x in raw["attachments"]],
            evidence_type=raw["evidence_type"],
            review_reason=raw["review_reason"],
            review_status=raw["review_status"],
        )
