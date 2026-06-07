# generated — do not edit
from __future__ import annotations

from enum import Enum


class ReviewStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


__all__ = [
    "ReviewStatus",
]
