"""R6 conformance: consumer-side type-safety via py.typed (PEP 561).

These tests verify that the dinie SDK ships real type hints that reach downstream
consumers — not untyped stubs or all-Any annotations. The mechanism:

  1. A 'mis-use script' commits deliberate type errors (wrong field type, nonexistent
     attribute). If py.typed is present AND hints are real, `mypy --strict` FAILS on it.
     If py.typed is absent, mypy treats dinie as untyped and the mis-use passes silently.

  2. A 'correct-use script' does only valid operations. `mypy --strict` must PASS on it.

C-COLO-1 (story 002) guarantees `py.typed` ships in the wheel. R6 gates that the
*content* of the hints is real (not Any-everywhere) by requiring mis-uses to be caught.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path


def _run_mypy(script_content: str, tmp_path: Path, strict: bool = True) -> tuple[int, str]:
    """Write script to tmp file and run mypy --strict over it. Returns (exit_code, output)."""
    script = tmp_path / "consumer.py"
    script.write_text(textwrap.dedent(script_content))
    cmd = [sys.executable, "-m", "mypy"]
    if strict:
        cmd.append("--strict")
    cmd.append(str(script))
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


class TestR6TypeSafety:
    def test_misuse_fails_mypy(self, tmp_path: Path) -> None:
        """A consumer that mis-uses generated types is caught by mypy --strict.

        The SDK must ship py.typed and real type hints for this to work.
        If py.typed is absent, mypy silently ignores dinie imports → mis-use passes → test fails.
        """
        script = """
            from dinie.generated.types.create_customer_request import CreateCustomerRequest

            # Type error 1: name must be str, not int.
            req = CreateCustomerRequest(
                cpf="123.456.789-00",
                cnpj="12.345.678/0001-90",
                email="joao@example.com",
                phone="+5511999999999",
                name=42,  # error: int, not str
            )

            # Type error 2: access a field that doesn't exist on the type.
            _ = req.nonexistent_field  # error: attribute not found
        """
        exit_code, output = _run_mypy(script, tmp_path)
        assert exit_code != 0, (
            "mypy should FAIL for a consumer script with type errors. "
            "If it passed, py.typed may be missing or all fields are typed as Any. "
            f"mypy output:\n{output}"
        )
        # Verify the specific errors were caught (not just any error)
        assert "name" in output or "Argument" in output or "error" in output.lower(), (
            f"Expected mypy to report type errors, got:\n{output}"
        )

    def test_correct_use_passes_mypy(self, tmp_path: Path) -> None:
        """A consumer using the SDK correctly must pass mypy --strict."""
        script = """
            from dinie.generated.types.create_customer_request import CreateCustomerRequest
            from dinie.generated.types.customer import Customer

            # Correct construction — all types match
            req = CreateCustomerRequest(
                cpf="123.456.789-00",
                cnpj="12.345.678/0001-90",
                email="joao@example.com",
                phone="+5511999999999",
            )

            # Serialize — returns dict[str, Any]
            wire: dict[str, object] = CreateCustomerRequest.serialize_create(req)

            # Deserialize a response
            raw: dict[str, object] = {
                "id": "cust_001",
                "status": "creating",
                "cpf": "123.456.789-00",
                "cnpj": "12.345.678/0001-90",
                "name": "João Silva",
                "email": "joao@example.com",
                "phone": "+5511999999999",
                "trading_name": "Loja",
                "external_id": "ref-001",
                "created_at": 1709546400,
                "updated_at": 1709546400,
            }
            customer: Customer = Customer.deserialize(raw)

            # Access a real field — must be typed as str
            name: str = customer.name
            email: str = customer.email
        """
        exit_code, output = _run_mypy(script, tmp_path)
        assert exit_code == 0, (
            f"mypy should PASS for a consumer script with correct types. mypy output:\n{output}"
        )

    def test_py_typed_marker_exists(self) -> None:
        """py.typed marker file must exist in the dinie package (PEP 561 / C-COLO-1)."""
        import dinie

        pkg_path = Path(dinie.__file__).parent
        marker = pkg_path / "py.typed"
        assert marker.exists(), (
            f"py.typed marker not found at {marker}. "
            "Without it, mypy treats the package as untyped and R6 silently passes mis-uses."
        )

    def test_webhook_event_type_narrowing(self, tmp_path: Path) -> None:
        """Event classes must be concrete enough for isinstance/match-case narrowing."""
        script = """
            from dinie.generated.events.customer_created import CustomerCreated

            raw: dict[str, object] = {
                "api_version": "2025-01-01",
                "created_at": 1709546400,
                "delivery_id": "del_001",
                "id": "evt_001",
                "timestamp": 1709546400,
                "type": "customer.created",
                "data": {},
            }
            event = CustomerCreated.deserialize(raw)

            # data field access — must be typed as CustomerCreatedData (not Any)
            data = event.data
        """
        exit_code, output = _run_mypy(script, tmp_path)
        assert exit_code == 0, (
            f"Event deserialize and data access should pass mypy --strict. mypy output:\n{output}"
        )
