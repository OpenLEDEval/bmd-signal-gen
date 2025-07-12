#!/usr/bin/env python3
"""
Type definitions for DeckLink SDK wrapper.
"""

import ctypes
from typing import Protocol

from .bmd_decklink import HDRMetadata


class DecklinkSDKProtocol(Protocol):
    """Protocol defining the interface for the DeckLink SDK wrapper."""

    # Device enumeration functions
    def decklink_get_device_count(self) -> int:
        """Get the number of available DeckLink devices."""
        ...

    def decklink_get_device_name_by_index(
        self, index: int, name_buffer: ctypes.Array[ctypes.c_char], buffer_size: int
    ) -> int:
        """Get device name by index."""
        ...

    # Device management functions
    def decklink_open_output_by_index(self, index: int) -> ctypes.c_void_p | None:
        """Open output device by index."""
        ...

    def decklink_close(self, handle: ctypes.c_void_p) -> None:
        """Close device handle."""
        ...

    # Output control functions
    def decklink_start_output(self, handle: ctypes.c_void_p) -> int:
        """Start output on device."""
        ...

    def decklink_stop_output(self, handle: ctypes.c_void_p) -> int:
        """Stop output on device."""
        ...

    # Pixel format functions
    def decklink_get_supported_pixel_format_count(self, handle: ctypes.c_void_p) -> int:
        """Get number of supported pixel formats."""
        ...

    def decklink_get_supported_pixel_format_name(
        self,
        handle: ctypes.c_void_p,
        index: int,
        name_buffer: ctypes.Array[ctypes.c_char],
        buffer_size: int,
    ) -> int:
        """Get supported pixel format name by index."""
        ...

    def decklink_set_pixel_format(
        self, handle: ctypes.c_void_p, format_index: int
    ) -> int:
        """Set pixel format by index."""
        ...

    def decklink_get_pixel_format(self, handle: ctypes.c_void_p) -> int:
        """Get current pixel format index."""
        ...

    # HDR metadata functions
    def decklink_set_eotf_metadata(
        self, handle: ctypes.c_void_p, eotf: int, max_cll: int, max_fall: int
    ) -> int:
        """Set EOTF metadata (legacy method)."""
        ...

    def decklink_set_hdr_metadata(
        self, handle: ctypes.c_void_p, metadata: ctypes.POINTER(HDRMetadata)
    ) -> int:
        """Set complete HDR metadata."""
        ...

    # Frame data management functions
    def decklink_set_frame_data(
        self,
        handle: ctypes.c_void_p,
        data: ctypes.POINTER(ctypes.c_uint16),
        width: int,
        height: int,
    ) -> int:
        """Set frame data."""
        ...

    # Frame management functions
    def decklink_create_frame_from_data(self, handle: ctypes.c_void_p) -> int:
        """Create frame from pending data."""
        ...

    def decklink_schedule_frame_for_output(self, handle: ctypes.c_void_p) -> int:
        """Schedule frame for output."""
        ...

    def decklink_start_scheduled_playback(self, handle: ctypes.c_void_p) -> int:
        """Start scheduled playback."""
        ...

    # Version info functions
    def decklink_get_driver_version(self) -> bytes:
        """Get driver version string."""
        ...

    def decklink_get_sdk_version(self) -> bytes:
        """Get SDK version string."""
        ...


# Type alias for the actual wrapper instance
DecklinkSDKWrapper: DecklinkSDKProtocol
