#!/usr/bin/env python3
"""
Python wrapper for DeckLink SDK.
"""

import ctypes
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from .decklink_types import DecklinkSDKProtocol


class PixelFormatType(Enum):
    """Enumeration of supported pixel format types."""

    FORMAT_8BIT_YUV = "2vuy"
    FORMAT_10BIT_YUV = "v210"
    FORMAT_10BIT_YUVA = "Ay10"
    FORMAT_8BIT_ARGB = 32
    FORMAT_8BIT_BGRA = "BGRA"
    FORMAT_10BIT_RGB = "r210"
    FORMAT_12BIT_RGB = "R12B"
    FORMAT_12BIT_RGBLE = "R12L"
    FORMAT_10BIT_RGBXLE = "R10l"
    FORMAT_10BIT_RGBX = "R10b"

    def __str__(self):
        return f"{self.name[8:]}"


class EOTFType(Enum):
    RESERVED = 0
    SDR = 1
    PQ = 2
    HLG = 3

    def __str__(self):
        return f"{self.value}={self.name}"

    @classmethod
    def parse(cls, value):
        # Try integer value
        try:
            return cls(int(value))
        except (ValueError, KeyError):
            pass
        # Try by name (case-insensitive)
        try:
            return cls[value.upper()]
        except KeyError:
            valid = ", ".join(f"{e.value} ({e.name})" for e in cls)
            raise ValueError(f"Invalid EOTF value: {value}. Use one of: {valid}")


# Complete HDR metadata structures (matching C++ implementation)
class ChromaticityCoordinates(ctypes.Structure):
    """Chromaticity coordinates for display primaries and white point."""

    _fields_ = [
        ("RedX", ctypes.c_double),
        ("RedY", ctypes.c_double),
        ("GreenX", ctypes.c_double),
        ("GreenY", ctypes.c_double),
        ("BlueX", ctypes.c_double),
        ("BlueY", ctypes.c_double),
        ("WhiteX", ctypes.c_double),
        ("WhiteY", ctypes.c_double),
    ]

    def __init__(
        self,
        red_xy: tuple[float, float],
        green_xy: tuple[float, float],
        blue_xy: tuple[float, float],
        white_xy: tuple[float, float],
    ):
        super().__init__()
        self.RedX = red_xy[0]
        self.RedY = red_xy[1]
        self.GreenX = green_xy[0]
        self.GreenY = green_xy[1]
        self.BlueX = blue_xy[0]
        self.BlueY = blue_xy[1]
        self.WhiteX = white_xy[0]
        self.WhiteY = white_xy[1]


# Standard chromaticity coordinates for common color spaces
CHROMATICITYCOORDINATES_REC709 = ChromaticityCoordinates(
    red_xy=(0.640, 0.330),    # Rec.709 Red
    green_xy=(0.300, 0.600),  # Rec.709 Green
    blue_xy=(0.150, 0.060),   # Rec.709 Blue
    white_xy=(0.3127, 0.3290) # D65 White Point
)

CHROMATICITYCOORDINATES_REC2020 = ChromaticityCoordinates(
    red_xy=(0.708, 0.292),    # Rec.2020 Red
    green_xy=(0.170, 0.797),  # Rec.2020 Green
    blue_xy=(0.131, 0.046),   # Rec.2020 Blue
    white_xy=(0.3127, 0.3290) # D65 White Point
)

CHROMATICITYCOORDINATES_DCI_P3 = ChromaticityCoordinates(
    red_xy=(0.680, 0.320),    # DCI-P3 Red
    green_xy=(0.265, 0.690),  # DCI-P3 Green
    blue_xy=(0.150, 0.060),   # DCI-P3 Blue
    white_xy=(0.3127, 0.3290) # D65 White Point (P3-D65)
)

CHROMATICITYCOORDINATES_REC601 = ChromaticityCoordinates(
    red_xy=(0.630, 0.340),    # Rec.601 Red
    green_xy=(0.310, 0.595),  # Rec.601 Green
    blue_xy=(0.155, 0.070),   # Rec.601 Blue
    white_xy=(0.3127, 0.3290) # D65 White Point
)


class HDRMetadata(ctypes.Structure):
    """Complete HDR metadata structure for DeckLink output.

    This structure defines HDR metadata including EOTF (Electro-Optical Transfer Function),
    display primaries, mastering display luminance, and content light levels.

    Args:
        eotf: EOTF type (0=Reserved, 1=SDR, 2=PQ, 3=HLG). Default is 3 (HLG).
        max_display_luminance: Maximum display mastering luminance in cd/m². Default is 1000.0.
        min_display_luminance: Minimum display mastering luminance in cd/m². Default is 0.0001.
        max_cll: Maximum Content Light Level in cd/m². Default is 1000.0.
        max_fall: Maximum Frame Average Light Level in cd/m². Default is 50.0.

    The structure automatically sets Rec2020 color primaries as defaults, matching
    the SignalGenHDR sample implementation.
    """

    _fields_ = [
        ("EOTF", ctypes.c_int64),
        ("referencePrimaries", ChromaticityCoordinates),
        ("maxDisplayMasteringLuminance", ctypes.c_double),
        ("minDisplayMasteringLuminance", ctypes.c_double),
        ("maxCLL", ctypes.c_double),
        ("maxFALL", ctypes.c_double),
    ]

    def __init__(
        self,
        eotf: int = 3,  # PQ
        max_display_luminance: float = 1000.0,
        min_display_luminance: float = 0.0001,
        max_cll: float = 1000.0,
        max_fall: float = 50.0,
    ):
        super().__init__()
        self.EOTF = eotf
        self.maxDisplayMasteringLuminance = max_display_luminance
        self.minDisplayMasteringLuminance = min_display_luminance
        self.maxCLL = max_cll
        self.maxFALL = max_fall

        # Set default Rec2020 primaries
        self.referencePrimaries = CHROMATICITYCOORDINATES_REC2020


def _configure_function_signatures(lib):
    """Configure ctypes function signatures for all DeckLink SDK functions."""

    # Device enumeration functions
    if hasattr(lib, "decklink_get_device_count"):
        lib.decklink_get_device_count.argtypes = []
        lib.decklink_get_device_count.restype = ctypes.c_int

    if hasattr(lib, "decklink_get_device_name_by_index"):
        lib.decklink_get_device_name_by_index.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
        ]
        lib.decklink_get_device_name_by_index.restype = ctypes.c_int

    # Device management functions
    if hasattr(lib, "decklink_open_output_by_index"):
        lib.decklink_open_output_by_index.argtypes = [ctypes.c_int]
        lib.decklink_open_output_by_index.restype = ctypes.c_void_p

    if hasattr(lib, "decklink_close"):
        lib.decklink_close.argtypes = [ctypes.c_void_p]
        lib.decklink_close.restype = None

    # Output control functions
    if hasattr(lib, "decklink_start_output"):
        lib.decklink_start_output.argtypes = [ctypes.c_void_p]
        lib.decklink_start_output.restype = ctypes.c_int

    if hasattr(lib, "decklink_stop_output"):
        lib.decklink_stop_output.argtypes = [ctypes.c_void_p]
        lib.decklink_stop_output.restype = ctypes.c_int

    # Pixel format functions
    if hasattr(lib, "decklink_get_supported_pixel_format_count"):
        lib.decklink_get_supported_pixel_format_count.argtypes = [ctypes.c_void_p]
        lib.decklink_get_supported_pixel_format_count.restype = ctypes.c_int

    if hasattr(lib, "decklink_get_supported_pixel_format_name"):
        lib.decklink_get_supported_pixel_format_name.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
        ]
        lib.decklink_get_supported_pixel_format_name.restype = ctypes.c_int

    if hasattr(lib, "decklink_set_pixel_format"):
        lib.decklink_set_pixel_format.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
        ]
        lib.decklink_set_pixel_format.restype = ctypes.c_int

    if hasattr(lib, "decklink_get_pixel_format"):
        lib.decklink_get_pixel_format.argtypes = [ctypes.c_void_p]
        lib.decklink_get_pixel_format.restype = ctypes.c_int

    # HDR metadata functions
    if hasattr(lib, "decklink_set_eotf_metadata"):
        lib.decklink_set_eotf_metadata.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_uint16,
            ctypes.c_uint16,
        ]
        lib.decklink_set_eotf_metadata.restype = ctypes.c_int

    if hasattr(lib, "decklink_set_hdr_metadata"):
        lib.decklink_set_hdr_metadata.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(HDRMetadata),
        ]
        lib.decklink_set_hdr_metadata.restype = ctypes.c_int

    # Frame data management functions
    if hasattr(lib, "decklink_set_frame_data"):
        lib.decklink_set_frame_data.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint16),
            ctypes.c_int,
            ctypes.c_int,
        ]
        lib.decklink_set_frame_data.restype = ctypes.c_int

    # Frame management functions
    if hasattr(lib, "decklink_create_frame_from_data"):
        lib.decklink_create_frame_from_data.argtypes = [ctypes.c_void_p]
        lib.decklink_create_frame_from_data.restype = ctypes.c_int

    if hasattr(lib, "decklink_schedule_frame_for_output"):
        lib.decklink_schedule_frame_for_output.argtypes = [ctypes.c_void_p]
        lib.decklink_schedule_frame_for_output.restype = ctypes.c_int

    if hasattr(lib, "decklink_start_scheduled_playback"):
        lib.decklink_start_scheduled_playback.argtypes = [ctypes.c_void_p]
        lib.decklink_start_scheduled_playback.restype = ctypes.c_int

    # Version info functions
    if hasattr(lib, "decklink_get_driver_version"):
        lib.decklink_get_driver_version.argtypes = []
        lib.decklink_get_driver_version.restype = ctypes.c_char_p

    if hasattr(lib, "decklink_get_sdk_version"):
        lib.decklink_get_sdk_version.argtypes = []
        lib.decklink_get_sdk_version.restype = ctypes.c_char_p


def _try_load_decklink_sdk() -> "DecklinkSDKProtocol":
    """Load the DeckLink SDK library and configure function signatures."""
    lib_path = Path(__file__).parent.joinpath("libdecklink.dylib")
    try:
        # Try to load from the lib directory relative to this script
        if lib_path.exists() and lib_path.is_file():
            decklink_lib = ctypes.CDLL(lib_path)
        else:
            raise FileNotFoundError(
                f"Could not find libdecklink.dylib in Python project: {lib_path.absolute()}"
            )
    except OSError as error:
        raise OSError(
            f"Failed to load DeckLink library from {lib_path.absolute()}"
        ) from error

    # Configure all function signatures
    _configure_function_signatures(decklink_lib)

    return decklink_lib  # type: ignore[return-value]


DecklinkSDKWrapper: "DecklinkSDKProtocol" = _try_load_decklink_sdk()


def get_decklink_driver_version():
    return DecklinkSDKWrapper.decklink_get_driver_version().decode("utf-8")


def get_decklink_sdk_version():
    return DecklinkSDKWrapper.decklink_get_sdk_version().decode("utf-8")


def get_decklink_devices():
    """Get list of available DeckLink device names."""
    count = DecklinkSDKWrapper.decklink_get_device_count()
    devices = []
    for i in range(count):
        name = ctypes.create_string_buffer(256)
        if DecklinkSDKWrapper.decklink_get_device_name_by_index(i, name, 256) == 0:
            devices.append(name.value.decode("utf-8"))
    return devices


class BMDDeckLink:
    """Minimal Python wrapper for DeckLink color patch output."""

    def __init__(self, device_index=0):
        self.handle = DecklinkSDKWrapper.decklink_open_output_by_index(device_index)
        if not self.handle:
            raise RuntimeError(
                f"No DeckLink output device found at index {device_index}"
            )
        self.started = False

    def close(self):
        """Close the device and free resources."""
        if self.handle:
            if self.started:
                DecklinkSDKWrapper.decklink_stop_output(self.handle)
            DecklinkSDKWrapper.decklink_close(self.handle)
            self.handle = None

    def start(self):
        """Start outputting the color patch."""
        if not self.handle:
            raise RuntimeError("Device not open")
        if self.started:
            return
        res = DecklinkSDKWrapper.decklink_start_output(self.handle)
        if res != 0:
            raise RuntimeError(f"Failed to start output (error {res})")
        self.started = True

    def stop(self):
        """Stop output."""
        if not self.handle or not self.started:
            return
        DecklinkSDKWrapper.decklink_stop_output(self.handle)
        self.started = False

    def get_supported_pixel_formats(self):
        """Get list of supported pixel format names."""
        if not self.handle:
            raise RuntimeError("Device not open")

        count = DecklinkSDKWrapper.decklink_get_supported_pixel_format_count(
            self.handle
        )
        formats = []
        for i in range(count):
            name = ctypes.create_string_buffer(256)
            if (
                DecklinkSDKWrapper.decklink_get_supported_pixel_format_name(
                    self.handle, i, name, 256
                )
                == 0
            ):
                formats.append(name.value.decode("utf-8"))
        return formats

    def set_pixel_format(self, format_index):
        """Set the pixel format by index."""
        if not self.handle:
            raise RuntimeError("Device not open")
        res = DecklinkSDKWrapper.decklink_set_pixel_format(self.handle, format_index)
        if res != 0:
            raise RuntimeError(f"Failed to set pixel format (error {res})")

    def get_pixel_format(self):
        """Get the current pixel format index."""
        if not self.handle:
            raise RuntimeError("Device not open")
        return DecklinkSDKWrapper.decklink_get_pixel_format(self.handle)

    def set_frame_eotf(self, eotf=0, maxCLL=0, maxFALL=0):
        """Set EOTF metadata for all future frames (legacy method)."""
        if not self.handle:
            raise RuntimeError("Device not open")
        res = DecklinkSDKWrapper.decklink_set_eotf_metadata(
            self.handle, eotf, maxCLL, maxFALL
        )
        if res != 0:
            raise RuntimeError(f"Failed to set EOTF metadata (error {res})")

    def set_hdr_metadata(self, metadata):
        """Set complete HDR metadata for all future frames.

        Args:
            metadata: HDRMetadata structure with complete HDR parameters
        """
        if not self.handle:
            raise RuntimeError("Device not open")
        res = DecklinkSDKWrapper.decklink_set_hdr_metadata(
            self.handle, ctypes.byref(metadata)
        )
        if res != 0:
            raise RuntimeError(f"Failed to set HDR metadata (error {res})")

    def set_frame_data(self, frame_data):
        """Set frame data from numpy array.

        Args:
            frame_data: numpy array with shape (height, width, channels) or (height, width)
        """
        if not self.handle:
            raise RuntimeError("Device not open")

        if not isinstance(frame_data, np.ndarray):
            raise ValueError("frame_data must be a numpy array")

        # Get dimensions
        if frame_data.ndim == 2:
            height, width = frame_data.shape
            channels = 1
        elif frame_data.ndim == 3:
            height, width, channels = frame_data.shape
        else:
            raise ValueError("frame_data must be 2D or 3D array")

        # Ensure data is uint16 and contiguous
        if frame_data.dtype != np.uint16:
            frame_data = frame_data.astype(np.uint16)
        frame_data = np.ascontiguousarray(frame_data)

        # Get pointer to data
        data_ptr = frame_data.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16))
        res = DecklinkSDKWrapper.decklink_set_frame_data(
            self.handle, data_ptr, width, height
        )
        if res != 0:
            raise RuntimeError(f"Failed to set frame data (error {res})")

    def create_frame(self):
        """Create a video frame from pending frame data."""
        if not self.handle:
            raise RuntimeError("Device not open")
        res = DecklinkSDKWrapper.decklink_create_frame_from_data(self.handle)
        if res != 0:
            raise RuntimeError(f"Failed to create frame (error {res})")

    def schedule_frame(self):
        """Schedule the current frame for output."""
        if not self.handle:
            raise RuntimeError("Device not open")
        res = DecklinkSDKWrapper.decklink_schedule_frame_for_output(self.handle)
        if res != 0:
            raise RuntimeError(f"Failed to schedule frame (error {res})")

    def start_playback(self):
        """Start scheduled playback."""
        if not self.handle:
            raise RuntimeError("Device not open")
        res = DecklinkSDKWrapper.decklink_start_scheduled_playback(self.handle)
        if res != 0:
            raise RuntimeError(f"Failed to start playback (error {res})")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
