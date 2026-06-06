"""Tests for dinie.runtime.models."""

from __future__ import annotations

from dinie.runtime.models import OMIT, Model, OmitType, _OmitType, serialize_request


class TestOmitSingleton:
    def test_singleton_identity(self) -> None:
        """_OmitType() always returns the same object."""
        assert _OmitType() is OMIT

    def test_omit_is_omittype(self) -> None:
        assert isinstance(OMIT, OmitType)

    def test_repr(self) -> None:
        assert repr(OMIT) == "OMIT"

    def test_str(self) -> None:
        assert str(OMIT) == "OMIT"

    def test_bool_is_false(self) -> None:
        """OMIT is falsy — makes `if value is OMIT` equivalent to `if not value`
        for typed callers, but identity check is the canonical form."""
        assert not bool(OMIT)

    def test_is_comparison(self) -> None:
        assert OMIT is OMIT  # trivial but docs intent

    def test_not_equal_to_none(self) -> None:
        assert OMIT is not None

    def test_not_equal_to_false(self) -> None:
        # OMIT is a distinct singleton, not False; cast to object to satisfy mypy
        omit_as_obj: object = OMIT
        assert omit_as_obj is not False


class TestModel:
    def test_model_is_base_marker(self) -> None:
        class MyModel(Model):
            pass

        obj = MyModel()
        assert isinstance(obj, Model)

    def test_model_itself_is_instantiatable(self) -> None:
        m = Model()
        assert isinstance(m, Model)


class TestSerializeRequest:
    def test_omit_fields_dropped(self) -> None:
        result = serialize_request({"a": 1, "b": OMIT, "c": "x"})
        assert result == {"a": 1, "c": "x"}

    def test_none_kept(self) -> None:
        result = serialize_request({"a": None, "b": OMIT})
        assert result == {"a": None}

    def test_empty_dict(self) -> None:
        assert serialize_request({}) == {}

    def test_all_omit(self) -> None:
        assert serialize_request({"a": OMIT, "b": OMIT}) == {}

    def test_no_omit(self) -> None:
        data = {"x": 1, "y": "hello", "z": False}
        assert serialize_request(data) == data

    def test_false_value_kept(self) -> None:
        """False is NOT OMIT — must survive serialization."""
        result = serialize_request({"flag": False})
        assert result == {"flag": False}

    def test_zero_kept(self) -> None:
        result = serialize_request({"count": 0})
        assert result == {"count": 0}

    def test_original_dict_not_mutated(self) -> None:
        original = {"a": OMIT, "b": 1}
        _ = serialize_request(original)
        assert "a" in original  # original unchanged
