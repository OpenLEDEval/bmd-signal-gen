"""
Global device state manager for BMD Signal Generator API.

This module provides a thread-safe singleton device manager that maintains
persistent device state across API requests. It leverages the existing
device management and pattern generation infrastructure while adding
the stateful management needed for web API operations.
"""

import threading
import time
from typing import Any

from bmd_sg.cli.shared import validate_color
from bmd_sg.decklink.bmd_decklink import BMDDeckLink, DecklinkSettings
from bmd_sg.image_generators.checkerboard import PatternGenerator


class APIDeviceManager:
    """
    Thread-safe singleton device manager for API server.

    Manages persistent device state including the DeckLink device connection,
    pattern generator, and current pattern configuration. Provides thread-safe
    methods for updating patterns and querying device status.

    Parameters
    ----------
    None

    Attributes
    ----------
    _device : BMDDeckLink | None
        Active DeckLink device instance
    _generator : PatternGenerator | None
        Pattern generator instance
    _settings : DecklinkSettings | None
        Current device configuration
    _current_colors : List[List[int]]
        Currently displayed pattern colors
    _lock : threading.Lock
        Thread synchronization lock
    _initialized : bool
        Whether the device manager has been initialized
    _start_time : float
        Server start timestamp for uptime calculation

    Examples
    --------
    Initialize device manager with CLI settings:
    >>> manager = APIDeviceManager()
    >>> manager.initialize(decklink, generator, settings)

    Update pattern colors:
    >>> new_colors = [[4095, 0, 0], [0, 4095, 0]]
    >>> manager.update_colors(new_colors)

    Get device status:
    >>> status = manager.get_status()
    >>> print(f"Device: {status['device_name']}")

    Notes
    -----
    This class implements the singleton pattern to ensure only one
    device manager instance exists across the API server lifetime.
    All device operations are protected by threading locks to prevent
    race conditions during concurrent API requests.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls) -> "APIDeviceManager":
        """
        Singleton pattern implementation.

        Returns
        -------
        APIDeviceManager
            The singleton device manager instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize device manager with default state."""
        if hasattr(self, "_initialized"):
            return

        self._device: BMDDeckLink | None = None
        self._generator: PatternGenerator | None = None
        self._settings: DecklinkSettings | None = None
        self._current_colors: list[list[int]] = []
        self._operation_lock = threading.Lock()
        self._initialized = False
        self._start_time = time.time()

    def initialize(
        self,
        device: BMDDeckLink,
        generator: PatternGenerator,
        settings: DecklinkSettings,
    ) -> None:
        """
        Initialize device manager with device instances.

        Parameters
        ----------
        device : BMDDeckLink
            Initialized DeckLink device instance
        generator : PatternGenerator
            Pattern generator instance configured for the device
        settings : DecklinkSettings
            Device configuration settings

        Raises
        ------
        RuntimeError
            If device manager is already initialized
        TypeError
            If any parameter is None or invalid type

        Examples
        --------
        >>> manager = APIDeviceManager()
        >>> manager.initialize(decklink, generator, settings)
        """
        with self._operation_lock:
            if self._initialized:
                raise RuntimeError("Device manager is already initialized")

            if device is None or generator is None or settings is None:
                raise TypeError("All parameters must be non-None")

            self._device = device
            self._generator = generator
            self._settings = settings
            self._current_colors = []
            self._initialized = True

    def is_initialized(self) -> bool:
        """
        Check if device manager is initialized.

        Returns
        -------
        bool
            True if device manager is initialized and ready
        """
        return self._initialized and self._device is not None

    def update_colors(self, colors: list[list[int]]) -> dict[str, Any]:
        """
        Update pattern colors with thread safety.

        Parameters
        ----------
        colors : List[List[int]]
            List of RGB color values. Each color is [R, G, B].

        Returns
        -------
        Dict[str, Any]
            Result dictionary with success status, message, and applied colors

        Raises
        ------
        RuntimeError
            If device manager is not initialized
        ValueError
            If color values are invalid for current bit depth

        Examples
        --------
        Update to white/black checkerboard:
        >>> result = manager.update_colors([[4095, 4095, 4095], [0, 0, 0]])
        >>> print(result['success'])  # True

        Single red color:
        >>> result = manager.update_colors([[4095, 0, 0]])
        """
        with self._operation_lock:
            if not self.is_initialized():
                return {
                    "success": False,
                    "message": "Device manager not initialized",
                    "updated_colors": [],
                }

            try:
                # Validate that we have proper instances
                if self._generator is None or self._device is None:
                    raise RuntimeError("Device or generator not properly initialized")

                # Validate colors against device bit depth
                for color in colors:
                    if len(color) != 3:
                        raise ValueError(
                            f"Color must have 3 values (RGB), got {len(color)}"
                        )

                    # Use existing validate_color function with device
                    validate_color(color, self._device)

                # Generate new pattern with validated colors
                image = self._generator.generate(colors)

                # Display the pattern
                self._device.display_frame(image)

                # Update stored state
                self._current_colors = colors.copy()

                return {
                    "success": True,
                    "message": f"Pattern updated successfully with {len(colors)} colors",
                    "updated_colors": self._current_colors,
                }

            except Exception as e:
                return {
                    "success": False,
                    "message": f"Failed to update colors: {e!s}",
                    "updated_colors": self._current_colors,
                }

    def get_status(self) -> dict[str, Any]:
        """
        Get current device and pattern status.

        Returns
        -------
        Dict[str, Any]
            Comprehensive status information including device, pattern, and HDR details

        Examples
        --------
        >>> status = manager.get_status()
        >>> print(f"Device: {status['device_name']}")
        >>> print(f"Resolution: {status['resolution']['width']}x{status['resolution']['height']}")
        """
        with self._operation_lock:
            if not self.is_initialized():
                return {
                    "device_connected": False,
                    "device_name": "No device",
                    "pixel_format": "Unknown",
                    "resolution": {"width": 0, "height": 0},
                    "current_pattern": {"type": "none", "colors": 0},
                    "hdr_enabled": False,
                    "hdr_metadata": {},
                }

            # Validate that we have proper instances
            if self._settings is None:
                raise RuntimeError("Settings not properly initialized")

            # Extract device information
            device_name = getattr(self._device, "device_name", "Unknown Device")
            pixel_format = (
                str(self._settings.pixel_format)
                if self._settings.pixel_format
                else "Auto"
            )

            # Build status response
            return {
                "device_connected": True,
                "device_name": device_name,
                "pixel_format": pixel_format,
                "resolution": {
                    "width": self._settings.width,
                    "height": self._settings.height,
                },
                "current_pattern": {
                    "type": "checkerboard",
                    "colors": len(self._current_colors),
                    "color_values": self._current_colors,
                },
                "hdr_enabled": not self._settings.no_hdr,
                "hdr_metadata": {
                    "eotf": str(self._settings.eotf),
                    "max_cll": self._settings.max_cll,
                    "max_fall": self._settings.max_fall,
                }
                if not self._settings.no_hdr
                else {},
            }

    def get_health(self) -> dict[str, Any]:
        """
        Get API server health information.

        Returns
        -------
        Dict[str, Any]
            Health status including uptime and basic device connectivity

        Examples
        --------
        >>> health = manager.get_health()
        >>> print(f"Status: {health['status']}")
        >>> print(f"Uptime: {health['uptime_seconds']:.1f}s")
        """
        return {
            "status": "healthy" if self.is_initialized() else "unhealthy",
            "version": "0.1.0",
            "uptime_seconds": time.time() - self._start_time,
        }

    def shutdown(self) -> None:
        """
        Clean shutdown of device resources.

        Safely closes the DeckLink device connection and cleans up resources.
        This method should be called during API server shutdown.

        Examples
        --------
        >>> manager.shutdown()
        """
        with self._operation_lock:
            if self._device is not None:
                # BMDDeckLink should handle cleanup via context manager or destructor
                self._device = None

            self._generator = None
            self._settings = None
            self._current_colors = []
            self._initialized = False


# Global singleton instance
device_manager = APIDeviceManager()


__all__ = ["APIDeviceManager", "device_manager"]
