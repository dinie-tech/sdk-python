# generated — do not edit
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ...runtime.webhooks import register_event
from .credit_offer_available import CreditOfferAvailable
from .credit_offer_expired import CreditOfferExpired
from .customer_active import CustomerActive
from .customer_created import CustomerCreated
from .customer_denied import CustomerDenied
from .customer_kyc_updated import CustomerKycUpdated
from .customer_under_review import CustomerUnderReview
from .loan_active import LoanActive
from .loan_cancelled import LoanCancelled
from .loan_created import LoanCreated
from .loan_error import LoanError
from .loan_finished import LoanFinished
from .loan_payment_received import LoanPaymentReceived
from .loan_processing import LoanProcessing
from .loan_signature_received import LoanSignatureReceived

WebhookEvent = (
    CreditOfferAvailable
    | CreditOfferExpired
    | CustomerActive
    | CustomerCreated
    | CustomerDenied
    | CustomerKycUpdated
    | CustomerUnderReview
    | LoanActive
    | LoanCancelled
    | LoanCreated
    | LoanError
    | LoanFinished
    | LoanPaymentReceived
    | LoanProcessing
    | LoanSignatureReceived
)

EVENT_DESERIALIZERS: dict[str, Callable[[dict[str, Any]], WebhookEvent]] = {
    "credit_offer.available": CreditOfferAvailable.deserialize,
    "credit_offer.expired": CreditOfferExpired.deserialize,
    "customer.active": CustomerActive.deserialize,
    "customer.created": CustomerCreated.deserialize,
    "customer.denied": CustomerDenied.deserialize,
    "customer.kyc_updated": CustomerKycUpdated.deserialize,
    "customer.under_review": CustomerUnderReview.deserialize,
    "loan.active": LoanActive.deserialize,
    "loan.cancelled": LoanCancelled.deserialize,
    "loan.created": LoanCreated.deserialize,
    "loan.error": LoanError.deserialize,
    "loan.finished": LoanFinished.deserialize,
    "loan.payment_received": LoanPaymentReceived.deserialize,
    "loan.processing": LoanProcessing.deserialize,
    "loan.signature_received": LoanSignatureReceived.deserialize,
}

# Populate the runtime webhook registry so runtime.webhooks.extract() can dispatch events.
for _event_type, _deserializer in EVENT_DESERIALIZERS.items():
    register_event(_event_type, _deserializer)

__all__ = [
    "CreditOfferAvailable",
    "CreditOfferExpired",
    "CustomerActive",
    "CustomerCreated",
    "CustomerDenied",
    "CustomerKycUpdated",
    "CustomerUnderReview",
    "LoanActive",
    "LoanCancelled",
    "LoanCreated",
    "LoanError",
    "LoanFinished",
    "LoanPaymentReceived",
    "LoanProcessing",
    "LoanSignatureReceived",
    "WebhookEvent",
    "EVENT_DESERIALIZERS",
]
