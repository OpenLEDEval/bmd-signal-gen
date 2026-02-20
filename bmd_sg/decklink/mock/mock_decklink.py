"""
Mock implementation of BMD DeckLink devices for development and testing.

This module provides a complete mock implementation of the BMDDeckLink class
and related module functions to enable development and testing without physical hardware.
"""

import contextlib
from typing import Any, ClassVar
from unittest.mock import MagicMock, patch

import numpy as np

from bmd_sg.decklink.bmd_decklink import (
    HDRMetadata,
    PixelFormatType,
)

# Global mock configuration state
_mock_config = {
    "available_devices": ["Mock DeckLink Device"],
    "supported_formats": [
        PixelFormatType.FORMAT_8BIT_YUV,
        PixelFormatType.FORMAT_10BIT_YUV,
        PixelFormatType.FORMAT_10BIT_RGB,
        PixelFormatType.FORMAT_12BIT_RGB,
        PixelFormatType.FORMAT_12BIT_RGBLE,
    ],
    "hdr_support": True,
    "driver_version": "12.8.1",
    "sdk_version": "15.3.0",
}


class MockBMDDeckLink:
    """
    Mock implementation of BMDDeckLink for development and testing without hardware.

    This class mimics the behavior of the real BMDDeckLink class while
    tracking all method calls and maintaining internal state for verification.

    Parameters
    ----------
    device_index : int, optional
        Index of the DeckLink device to simulate. Default is 0.

    Attributes
    ----------
    device_index : int
        Index of the simulated device
    device_name : str
        Name of the simulated device
    handle : object
        Mock handle object (always non-None when open)
    started : bool
        Whether playback has been started
    _pixel_format : PixelFormatType
        Current pixel format setting
    _hdr_metadata : HDRMetadata | None
        Current HDR metadata settings
    _frame_history : list
        History of displayed frames for verification
    _method_calls : dict
        Tracking of all method calls for verification

    Examples
    --------
    Basic usage:
    >>> device = MockBMDDeckLink(0)
    >>> device.start_playback()
    >>> device.display_frame(frame_data)
    >>> device.close()

    Context manager usage:
    >>> with MockBMDDeckLink(0) as device:
    ...     device.start_playback()
    ...     # Device automatically closed

    Development usage:
    >>> from bmd_sg.decklink.mock import MockBMDDeckLink
    >>> device = MockBMDDeckLink(0)  # Virtual device for development
    """

    _instances: ClassVar[list["MockBMDDeckLink"]] = []

    def __init__(self, device_index: int = 0) -> None:
        # Check if device exists in mock configuration
        if device_index >= len(_mock_config["available_devices"]):
            raise RuntimeError(
                f"No DeckLink output device found at index {device_index}"
            )

        self.device_index = device_index
        self.device_name = _mock_config["available_devices"][device_index]
        self.handle = MagicMock()  # Always non-None when device is "open"
        self.started = False

        # Internal state
        self._pixel_format = _mock_config["supported_formats"][0]
        self._hdr_metadata: HDRMetadata | None = None
        self._frame_history: list[np.ndarray] = []
        self._max_frame_history = 10

        # Method call tracking
        self._method_calls: dict[str, list[dict[str, Any]]] = {
            "start_playback": [],
            "stop_playback": [],
            "set_pixel_format": [],
            "set_hdr_metadata": [],
            "display_frame": [],
            "close": [],
        }

        # Track instance for cleanup
        MockBMDDeckLink._instances.append(self)

    def __del__(self) -> None:
        """Destructor - automatically close device on object destruction."""
        if hasattr(self, "handle"):
            self.close()

    def __enter__(self) -> "MockBMDDeckLink":
        """Enter the context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any | None,
    ) -> None:
        """Exit the context manager and close the device."""
        self.close()

    def close(self) -> None:
        """Close the device and free resources."""
        if self.handle:
            self._method_calls["close"].append({})
            if self.started:
                self.stop_playback()
            self.handle = None
            # Remove from instances list
            if self in MockBMDDeckLink._instances:
                MockBMDDeckLink._instances.remove(self)

    @property
    def is_open(self) -> bool:
        """Check if the device is currently open."""
        return self.handle is not None

    def start_playback(self) -> None:
        """Start playback output to the DeckLink device."""
        if not self.handle:
            raise RuntimeError("Device not open")
        if self.started:
            return

        self._method_calls["start_playback"].append({})
        self.started = True

    def stop_playback(self) -> None:
        """Stop playback output from the DeckLink device."""
        if not self.handle or not self.started:
            return

        self._method_calls["stop_playback"].append({})
        self.started = False

    def get_supported_pixel_formats(self) -> list[PixelFormatType]:
        """Get list of supported pixel format enum values."""
        if not self.handle:
            raise RuntimeError("Device not open")
        return _mock_config["supported_formats"].copy()

    @property
    def supports_hdr(self) -> bool:
        """Check if the device supports HDR."""
        return _mock_config["hdr_support"]

    @property
    def pixel_format(self) -> PixelFormatType:
        """Get the current pixel format."""
        if not self.handle:
            raise RuntimeError("Device not open")
        return self._pixel_format

    @pixel_format.setter
    def pixel_format(self, pixel_format_type: PixelFormatType) -> None:
        """Set the pixel format."""
        if not self.handle:
            raise RuntimeError("Device not open")

        # Validate format is supported
        if pixel_format_type not in _mock_config["supported_formats"]:
            raise RuntimeError(
                f"Failed to set pixel format {pixel_format_type.name} (error -1)"
            )

        self._method_calls["set_pixel_format"].append({"format": pixel_format_type})
        self._pixel_format = pixel_format_type

    def set_hdr_metadata(self, metadata: HDRMetadata) -> None:
        """Set complete HDR metadata for all future frames."""
        if not self.handle:
            raise RuntimeError("Device not open")

        if not self.supports_hdr:
            raise RuntimeError("Failed to set HDR metadata (error -1)")

        self._method_calls["set_hdr_metadata"].append({"metadata": metadata})
        self._hdr_metadata = metadata

    def display_frame(self, frame_data: np.ndarray) -> None:
        """Display a single frame synchronously."""
        if not self.handle:
            raise RuntimeError("Device not open")

        # Validate frame data
        if not isinstance(frame_data, np.ndarray):
            raise ValueError("frame_data must be a numpy array")

        # Convert and validate as the real implementation does
        frame_data = np.astype(frame_data, np.uint16, copy=True)
        frame_data = np.ascontiguousarray(frame_data)

        # Store frame in history
        self._frame_history.append(frame_data.copy())
        if len(self._frame_history) > self._max_frame_history:
            self._frame_history.pop(0)

        # Track method call
        self._method_calls["display_frame"].append(
            {"shape": frame_data.shape, "dtype": frame_data.dtype}
        )

    # Additional mock-specific methods for testing and verification

    def get_method_calls(
        self, method_name: str | None = None
    ) -> list[dict[str, Any]] | dict[str, list[dict[str, Any]]]:
        """
        Get history of method calls for verification.

        Parameters
        ----------
        method_name : str, optional
            Specific method to get calls for. If None, returns all calls.

        Returns
        -------
        list or dict
            List of call info for specific method, or dict of all calls
        """
        if method_name:
            return self._method_calls.get(method_name, [])
        return self._method_calls.copy()

    def get_frame_history(self) -> list[np.ndarray]:
        """Get history of displayed frames."""
        return self._frame_history.copy()

    def get_last_frame(self) -> np.ndarray | None:
        """Get the last displayed frame."""
        return self._frame_history[-1] if self._frame_history else None

    def clear_history(self) -> None:
        """Clear method call and frame history."""
        for key in self._method_calls:
            self._method_calls[key] = []
        self._frame_history = []


# Mock module-level functions


def mock_get_decklink_devices() -> list[str]:
    """Mock implementation of get_decklink_devices."""
    return _mock_config["available_devices"].copy()


def mock_get_decklink_driver_version() -> str:
    """Mock implementation of get_decklink_driver_version."""
    return _mock_config["driver_version"]


def mock_get_decklink_sdk_version() -> str:
    """Mock implementation of get_decklink_sdk_version."""
    return _mock_config["sdk_version"]


# Configuration functions


def set_available_devices(devices: list[str]) -> None:
    """
    Configure the list of available mock devices.

    Parameters
    ----------
    devices : list[str]
        List of device names to make available
    """
    _mock_config["available_devices"] = devices.copy()


def set_supported_formats(formats: list[PixelFormatType]) -> None:
    """
    Configure supported pixel formats for mock devices.

    Parameters
    ----------
    formats : list[PixelFormatType]
        List of pixel formats to support
    """
    _mock_config["supported_formats"] = formats.copy()


def set_hdr_support(enabled: bool) -> None:
    """
    Configure HDR support for mock devices.

    Parameters
    ----------
    enabled : bool
        Whether mock devices should support HDR
    """
    _mock_config["hdr_support"] = enabled


def reset_mock_state() -> None:
    """Reset all mock configuration to defaults and close any open devices."""
    # Close all open mock devices
    for device in MockBMDDeckLink._instances[:]:
        device.close()

    # Reset configuration
    _mock_config.update(
        {
            "available_devices": ["Mock DeckLink Device"],
            "supported_formats": [
                PixelFormatType.FORMAT_8BIT_YUV,
                PixelFormatType.FORMAT_10BIT_YUV,
                PixelFormatType.FORMAT_10BIT_RGB,
                PixelFormatType.FORMAT_12BIT_RGB,
                PixelFormatType.FORMAT_12BIT_RGBLE,
            ],
            "hdr_support": True,
            "driver_version": "12.8.1",
            "sdk_version": "15.3.0",
        }
    )


# Patching utilities


@contextlib.contextmanager
def patch_decklink_module():
    """
    Context manager to patch the decklink module with mocks.

    This patches the BMDDeckLink class and module functions to use
    mock implementations. Useful for testing without hardware.

    Examples
    --------
    >>> with patch_decklink_module():
    ...     device = BMDDeckLink(0)  # Uses MockBMDDeckLink
    ...     devices = get_decklink_devices()  # Uses mock function
    """
    patches = [
        patch("bmd_sg.decklink.bmd_decklink.BMDDeckLink", MockBMDDeckLink),
        patch(
            "bmd_sg.decklink.bmd_decklink.get_decklink_devices",
            mock_get_decklink_devices,
        ),
        patch(
            "bmd_sg.decklink.bmd_decklink.get_decklink_driver_version",
            mock_get_decklink_driver_version,
        ),
        patch(
            "bmd_sg.decklink.bmd_decklink.get_decklink_sdk_version",
            mock_get_decklink_sdk_version,
        ),
        # Also patch the SDK wrapper to prevent real library loading
        patch("bmd_sg.decklink.bmd_decklink.DecklinkSDKWrapper", MagicMock()),
    ]

    with contextlib.ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        yield
