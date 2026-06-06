"""Dinie Python SDK.

Official SDK for the Dinie V3 API. Import the client and call it:

    import dinie
    client = dinie.Dinie(client_id="...", client_secret="...")

The generated layer (resources, types, events) is populated by the generator
(story 007). Until then only the version constant and py.typed marker ship.
"""

__version__ = "0.5.0"

# C-COLO-2: __version__ is the single source of truth.
# The runtime User-Agent header ("Dinie-SDK-Python/<ver>") reads from here.

__all__ = ["__version__"]
