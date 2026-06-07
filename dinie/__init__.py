"""Dinie Python SDK.

Official SDK for the Dinie V3 API. Import the client and call it:

    import dinie
    client = dinie.Dinie(client_id="...", client_secret="...")

Webhook events:

    from dinie.webhooks import extract
    event = extract(payload, headers)
    match event:
        case dinie.CustomerCreatedEvent(): ...
"""
from __future__ import annotations

from dinie.generated.client import Dinie
from dinie.generated.events import WebhookEvent
from dinie.generated.events.credit_offer_available import CreditOfferAvailable
from dinie.generated.events.credit_offer_expired import CreditOfferExpired
from dinie.generated.events.customer_active import CustomerActive
from dinie.generated.events.customer_created import CustomerCreated
from dinie.generated.events.customer_denied import CustomerDenied
from dinie.generated.events.customer_kyc_updated import CustomerKycUpdated
from dinie.generated.events.customer_under_review import CustomerUnderReview
from dinie.generated.events.loan_active import LoanActive
from dinie.generated.events.loan_cancelled import LoanCancelled
from dinie.generated.events.loan_created import LoanCreated
from dinie.generated.events.loan_error import LoanError
from dinie.generated.events.loan_finished import LoanFinished
from dinie.generated.events.loan_payment_received import LoanPaymentReceived
from dinie.generated.events.loan_processing import LoanProcessing
from dinie.generated.events.loan_signature_received import LoanSignatureReceived
from dinie.runtime.errors import ApiError

__version__ = "0.5.0"

# C-COLO-2: __version__ is the single source of truth.
# The runtime User-Agent header ("Dinie-SDK-Python/<ver>") reads from here.

__all__ = [
    "__version__",
    "Dinie",
    "WebhookEvent",
    # Event types (for match/case and isinstance checks)
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
    # Errors
    "ApiError",
]
