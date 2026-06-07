# generated — do not edit
from __future__ import annotations

from typing import Any

from .fixed_installment_credit_offer import FixedInstallmentCreditOffer
from .range_installment_credit_offer import RangeInstallmentCreditOffer

CreditOffer = FixedInstallmentCreditOffer | RangeInstallmentCreditOffer


def deserialize_credit_offer(raw: dict[str, Any]) -> CreditOffer:
    """Dispatch by field presence (no `discriminator` keyword).

    Each variant is identified by its required fields.
    """
    if "installments" in raw:
        return FixedInstallmentCreditOffer.deserialize(raw)
    elif "max_installments" in raw:
        return RangeInstallmentCreditOffer.deserialize(raw)

    else:
        # Fallback: use the last variant when no presence key matches.
        return RangeInstallmentCreditOffer.deserialize(raw)


__all__ = ["CreditOffer", "deserialize_credit_offer"]
