"""
DeckLink SDK wrapper and utilities.

Python interface to the Blackmagic Design DeckLink SDK for professional
video output with HDR metadata support.

This module also provides mock implementations for development and testing
without requiring physical hardware.
"""

# Main DeckLink exports
from bmd_sg.decklink.bmd_decklink import (
    BMDDeckLink,
    DecklinkSettings,
    EOTFType,
    HDRMetadata,
    PixelFormatType,
    get_decklink_devices,
    get_decklink_driver_version,
    get_decklink_sdk_version,
)

__all__ = [
    "BMDDeckLink",
    "DecklinkSettings",
    "EOTFType",
    "HDRMetadata",
    "PixelFormatType",
    "get_decklink_devices",
    "get_decklink_driver_version",
    "get_decklink_sdk_version",
]

# Optional mock exports for development/testing
try:
    from bmd_sg.decklink.mock import (  # noqa: F401
        MockBMDDeckLink,
        patch_decklink_module,
        reset_mock_state,
        set_available_devices,
        set_hdr_support,
        set_supported_formats,
    )

    __all__.extend(
        [
            "MockBMDDeckLink",
            "patch_decklink_module",
            "reset_mock_state",
            "set_available_devices",
            "set_hdr_support",
            "set_supported_formats",
        ]
    )
except ImportError:
    # Mock module not available - this is fine for production use
    pass
