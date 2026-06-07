"""R1 conformance: round-trip serialize/deserialize against OpenAPI spec examples.

These examples are taken verbatim from the openapi.yaml request/response `example:` blocks.
The goal is to verify that:
  - request types constructed via kwargs serialize to the exact wire dict (no extra null fields)
  - response examples deserialize to typed models with correct field values
    (epochs remain int, nested types become dataclasses, optional-absent ≠ explicit None)
"""

from __future__ import annotations

import pytest

from dinie.generated.types.biometrics_session import BiometricsSession
from dinie.generated.types.create_credential_request import CreateCredentialRequest
from dinie.generated.types.create_customer_request import CreateCustomerRequest
from dinie.generated.types.create_loan_request import CreateLoanRequest
from dinie.generated.types.create_simulation_request import CreateSimulationRequest
from dinie.generated.types.create_webhook_endpoint_request import CreateWebhookEndpointRequest
from dinie.generated.types.customer import Customer
from dinie.generated.types.kyc_attachment_response import KycAttachmentResponse
from dinie.generated.types.loan import Loan
from dinie.generated.types.simulation import Simulation
from dinie.generated.types.update_customer_request import UpdateCustomerRequest


# ── Request serialize ─────────────────────────────────────────────────────────

class TestSerializeRoundTrip:
    """Each request type's serialize_* method must produce the exact wire dict
    that matches the OpenAPI request-body example."""

    def test_create_credential_with_expires_at(self) -> None:
        """CreateCredentialRequest (name + expires_at) → both fields present in wire dict."""
        req = CreateCredentialRequest(name="Chave de Produção", expires_at=1803945600)
        wire = CreateCredentialRequest.serialize_create(req)
        assert wire == {"name": "Chave de Produção", "expires_at": 1803945600}

    def test_create_credential_omits_absent_optional(self) -> None:
        """Optional expires_at absent → not serialized as null, fully omitted."""
        req = CreateCredentialRequest(name="Chave de Produção")
        wire = CreateCredentialRequest.serialize_create(req)
        assert wire == {"name": "Chave de Produção"}
        assert "expires_at" not in wire

    def test_create_customer_request(self) -> None:
        """CreateCustomerRequest spec example (all required + optional external_id)."""
        req = CreateCustomerRequest(
            cpf="123.456.789-00",
            cnpj="12.345.678/0001-90",
            email="joao@example.com",
            phone="+5511999999999",
            external_id="partner-ref-123",
        )
        wire = CreateCustomerRequest.serialize_create(req)
        assert wire == {
            "cpf": "123.456.789-00",
            "cnpj": "12.345.678/0001-90",
            "email": "joao@example.com",
            "phone": "+5511999999999",
            "external_id": "partner-ref-123",
        }

    def test_create_customer_omits_absent_optional(self) -> None:
        """CreateCustomerRequest without optional name/external_id → absent from wire dict."""
        req = CreateCustomerRequest(
            cpf="123.456.789-00",
            cnpj="12.345.678/0001-90",
            email="joao@example.com",
            phone="+5511999999999",
        )
        wire = CreateCustomerRequest.serialize_create(req)
        assert "name" not in wire
        assert "external_id" not in wire

    def test_update_customer_request(self) -> None:
        """UpdateCustomerRequest spec example (partial update: email + phone only)."""
        req = UpdateCustomerRequest(email="joao.novo@example.com", phone="+5511988887777")
        wire = UpdateCustomerRequest.serialize_update(req)
        assert wire == {"email": "joao.novo@example.com", "phone": "+5511988887777"}

    def test_update_customer_omits_absent_optional(self) -> None:
        """UpdateCustomerRequest with only email → phone absent from wire dict (not null)."""
        req = UpdateCustomerRequest(email="joao.novo@example.com")
        wire = UpdateCustomerRequest.serialize_update(req)
        assert wire == {"email": "joao.novo@example.com"}
        assert "phone" not in wire

    def test_create_webhook_endpoint_request(self) -> None:
        """CreateWebhookEndpointRequest spec example (url + events + description)."""
        req = CreateWebhookEndpointRequest(
            url="https://parceiro.example.com/webhooks/dinie",
            events=["customer.active", "credit_offer.available", "loan.*"],
            description="Webhook de produção",
        )
        wire = CreateWebhookEndpointRequest.serialize_create(req)
        assert wire == {
            "url": "https://parceiro.example.com/webhooks/dinie",
            "events": ["customer.active", "credit_offer.available", "loan.*"],
            "description": "Webhook de produção",
        }

    def test_create_webhook_omits_absent_optional(self) -> None:
        """CreateWebhookEndpointRequest with only url → events/description absent."""
        req = CreateWebhookEndpointRequest(url="https://parceiro.example.com/webhooks/dinie")
        wire = CreateWebhookEndpointRequest.serialize_create(req)
        assert wire == {"url": "https://parceiro.example.com/webhooks/dinie"}
        assert "events" not in wire
        assert "description" not in wire

    def test_create_loan_request(self) -> None:
        """CreateLoanRequest spec example (all required fields)."""
        req = CreateLoanRequest(
            credit_offer_id="co_550e8400e29b41d4a716446655440000",
            simulation_id="sim_550e8400e29b41d4a716446655440001",
            installment_count=4,
            installment_amount=7997.34,
            first_due_date="2026-04-03",
        )
        wire = CreateLoanRequest.serialize_create(req)
        assert wire == {
            "credit_offer_id": "co_550e8400e29b41d4a716446655440000",
            "simulation_id": "sim_550e8400e29b41d4a716446655440001",
            "installment_count": 4,
            "installment_amount": 7997.34,
            "first_due_date": "2026-04-03",
        }

    def test_create_simulation_request(self) -> None:
        """CreateSimulationRequest spec example (requested_amount + installment_count)."""
        req = CreateSimulationRequest(
            requested_amount=25000.00,
            installment_count=4,
        )
        wire = CreateSimulationRequest.serialize_create_simulation(req)
        assert wire == {"requested_amount": 25000.00, "installment_count": 4}


# ── Response deserialize ──────────────────────────────────────────────────────

class TestDeserializeRoundTrip:
    """Each response type must deserialize the OpenAPI response example to a
    typed model with exact field values."""

    def test_customer_deserialize(self) -> None:
        """Customer spec example (UpdateCustomer response — all required fields populated)."""
        raw: dict = {
            "id": "cust_550e8400e29b41d4a716446655440000",
            "status": "active",
            "cpf": "123.456.789-00",
            "cnpj": "12.345.678/0001-90",
            "name": "João Silva",
            "email": "joao.novo@example.com",
            "phone": "+5511988887777",
            "trading_name": "Loja do João",
            "external_id": "partner-ref-123",
            "kyc": [],
            "created_at": 1709546400,
            "updated_at": 1709632800,
        }
        customer = Customer.deserialize(raw)
        assert customer.id == "cust_550e8400e29b41d4a716446655440000"
        assert customer.status == "active"
        assert customer.cpf == "123.456.789-00"
        assert customer.name == "João Silva"
        assert customer.trading_name == "Loja do João"
        # epoch stays int (not converted to datetime)
        assert isinstance(customer.created_at, int)
        assert customer.created_at == 1709546400
        # kyc list empty but not None
        assert customer.kyc == []

    def test_biometrics_session_deserialize(self) -> None:
        """BiometricsSession spec example."""
        raw = {
            "session_url": "https://kyc-app.dinie.com.br/session/dinie_bsc_test_abc123def456",
            "expires_at": 1741082400,
        }
        session = BiometricsSession.deserialize(raw)
        assert session.session_url == "https://kyc-app.dinie.com.br/session/dinie_bsc_test_abc123def456"
        assert isinstance(session.expires_at, int)
        assert session.expires_at == 1741082400

    def test_kyc_attachment_response_deserialize(self) -> None:
        """KycAttachmentResponse spec example."""
        raw = {"attachment_type": "photo", "submitted": True}
        resp = KycAttachmentResponse.deserialize(raw)
        assert resp.attachment_type == "photo"
        assert resp.submitted is True

    def test_loan_deserialize(self) -> None:
        """Loan spec example (CreateLoan response — float fields, string date, epoch ints)."""
        raw: dict = {
            "id": "ln_550e8400e29b41d4a716446655440001",
            "credit_offer_id": "co_550e8400e29b41d4a716446655440000",
            "customer_id": "cust_550e8400e29b41d4a716446655440000",
            "simulation_id": "sim_550e8400e29b41d4a716446655440001",
            "status": "awaiting_signatures",
            "requested_amount": 25000.00,
            "principal_amount": 29375.00,
            "iof_amount": 1875.00,
            "monthly_interest_rate": 3.50,
            "annual_interest_rate": 51.11,
            "monthly_cet_rate": 2.00,
            "annual_cet_rate": 233.18,
            "total_amount": 31989.36,
            "installment_amount": 7997.34,
            "first_due_date": "2026-04-03",
            "installment_count": 4,
            "ccb_number": "CCB-2026-001234",
            "disbursement_method": "pix",
            "signing_url": "https://clicksign.com/widget/...",
            "created_at": 1709550000,
            "updated_at": 1709550000,
        }
        loan = Loan.deserialize(raw)
        assert loan.id == "ln_550e8400e29b41d4a716446655440001"
        assert loan.status == "awaiting_signatures"
        assert loan.requested_amount == 25000.00
        assert loan.first_due_date == "2026-04-03"  # date stays as string (not date object)
        assert isinstance(loan.created_at, int)      # epoch stays int
        assert loan.installment_count == 4

    def test_simulation_deserialize(self) -> None:
        """Simulation spec example (CreateSimulation response — many float fields)."""
        raw: dict = {
            "id": "sim_550e8400e29b41d4a716446655440001",
            "credit_offer_id": "co_550e8400e29b41d4a716446655440000",
            "requested_amount": 25000.00,
            "principal_amount": 29375.00,
            "interest_amount": 2614.36,
            "iof_amount": 1875.00,
            "fee_amount": 2500.00,
            "total_amount": 31989.36,
            "monthly_interest_rate": 3.50,
            "annual_interest_rate": 51.11,
            "monthly_cet_rate": 2.00,
            "annual_cet_rate": 233.18,
            "installment_count": 4,
            "installment_amount": 7997.34,
            "first_due_date": "2026-04-03",
            "created_at": 1709548200,
        }
        sim = Simulation.deserialize(raw)
        assert sim.id == "sim_550e8400e29b41d4a716446655440001"
        assert sim.requested_amount == 25000.00
        assert sim.installment_count == 4
        assert sim.first_due_date == "2026-04-03"
        assert isinstance(sim.created_at, int)

    def test_optional_absent_is_none_not_explicit(self) -> None:
        """Optional fields absent from wire dict → None in model (not the same as 'key=null').
        This guards against lazy deserializers that treat absent == explicit null."""
        req = CreateCredentialRequest.deserialize({"name": "Key"})
        assert req.expires_at is None
        # The serialized form must NOT include the absent optional:
        wire = CreateCredentialRequest.serialize_create(req)
        assert "expires_at" not in wire


# ── Parametric coverage: all request types with their spec examples ───────────

REQUEST_EXAMPLES = [
    pytest.param(
        CreateCredentialRequest,
        "serialize_create",
        {"name": "Chave de Produção", "expires_at": 1803945600},
        {"name": "Chave de Produção", "expires_at": 1803945600},
        id="CreateCredentialRequest/spec-example",
    ),
    pytest.param(
        CreateCustomerRequest,
        "serialize_create",
        {
            "cpf": "123.456.789-00",
            "cnpj": "12.345.678/0001-90",
            "email": "joao@example.com",
            "phone": "+5511999999999",
            "external_id": "partner-ref-123",
        },
        {
            "cpf": "123.456.789-00",
            "cnpj": "12.345.678/0001-90",
            "email": "joao@example.com",
            "phone": "+5511999999999",
            "external_id": "partner-ref-123",
        },
        id="CreateCustomerRequest/spec-example",
    ),
    pytest.param(
        UpdateCustomerRequest,
        "serialize_update",
        {"email": "joao.novo@example.com", "phone": "+5511988887777"},
        {"email": "joao.novo@example.com", "phone": "+5511988887777"},
        id="UpdateCustomerRequest/spec-example",
    ),
    pytest.param(
        CreateWebhookEndpointRequest,
        "serialize_create",
        {
            "url": "https://parceiro.example.com/webhooks/dinie",
            "events": ["customer.active", "credit_offer.available", "loan.*"],
            "description": "Webhook de produção",
        },
        {
            "url": "https://parceiro.example.com/webhooks/dinie",
            "events": ["customer.active", "credit_offer.available", "loan.*"],
            "description": "Webhook de produção",
        },
        id="CreateWebhookEndpointRequest/spec-example",
    ),
    pytest.param(
        CreateLoanRequest,
        "serialize_create",
        {
            "credit_offer_id": "co_550e8400e29b41d4a716446655440000",
            "simulation_id": "sim_550e8400e29b41d4a716446655440001",
            "installment_count": 4,
            "installment_amount": 7997.34,
            "first_due_date": "2026-04-03",
        },
        {
            "credit_offer_id": "co_550e8400e29b41d4a716446655440000",
            "simulation_id": "sim_550e8400e29b41d4a716446655440001",
            "installment_count": 4,
            "installment_amount": 7997.34,
            "first_due_date": "2026-04-03",
        },
        id="CreateLoanRequest/spec-example",
    ),
]


@pytest.mark.parametrize("cls,method,kwargs,expected_wire", REQUEST_EXAMPLES)
def test_request_serialize_matches_spec_example(cls, method, kwargs, expected_wire):  # type: ignore[no-untyped-def]
    """For each request type's spec example: deserialize the raw kwargs dict to construct
    the typed model (using the same field names), then serialize and compare to expected wire."""
    instance = cls.deserialize(kwargs)
    serializer = getattr(cls, method)
    wire = serializer(instance)
    assert wire == expected_wire
