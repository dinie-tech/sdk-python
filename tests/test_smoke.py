"""Smoke test: verify the package is importable and __version__ is set.

This is the trivial green gate that keeps CI honest before the runtime
(stories 003/004) and generated layer (story 007) land.
"""

import dinie


def test_version_is_set() -> None:
    """__version__ must be a non-empty string (C-COLO-2)."""
    assert isinstance(dinie.__version__, str)
    assert dinie.__version__ != ""
