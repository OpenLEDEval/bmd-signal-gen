"""
Mock DeckLink devices for development and testing.

This module provides mock implementations of DeckLink devices and related
functionality to enable development and testing without physical hardware.

Examples
--------
Basic mock device usage:
>>> from bmd_sg.decklink.mock import MockBMDDeckLink
>>> device = MockBMDDeckLink(0)
>>> device.start_playback()

CLI with mock device:
>>> # bmd-signal-gen --mock-device solid --color 4095 0 0

Development workflow:
>>> from bmd_sg.decklink.mock import patch_decklink_module
>>> with patch_decklink_module():
...     # All DeckLink operations use mocks
...     from bmd_sg.decklink.bmd_decklink import BMDDeckLink
...     device = BMDDeckLink(0)  # Actually creates MockBMDDeckLink
"""

from bmd_sg.decklink.mock.mock_decklink import (
    MockBMDDeckLink,
    mock_get_decklink_devices,
    mock_get_decklink_driver_version,
    mock_get_decklink_sdk_version,
    patch_decklink_module,
    reset_mock_state,
    set_available_devices,
    set_hdr_support,
    set_supported_formats,
)

__all__ = [
    "MockBMDDeckLink",
    "mock_get_decklink_devices",
    "mock_get_decklink_driver_version",
    "mock_get_decklink_sdk_version",
    "patch_decklink_module",
    "reset_mock_state",
    "set_available_devices",
    "set_hdr_support",
    "set_supported_formats",
]
