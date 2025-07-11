#!/usr/bin/env python3
"""
Python wrapper for Blackmagic Design DeckLink SDK.

This module provides a Python interface to the Blackmagic Design DeckLink SDK,
enabling direct control of DeckLink devices for professional video output.
The module supports HDR metadata, various pixel formats, and comprehensive
device management.

The module includes:
- ctypes-based wrapper for the DeckLink SDK C++ library
- HDR metadata structures with standard color space definitions
- Device enumeration and management
- Frame data handling with numpy integration
- Complete type definitions for better IDE support

Examples
--------
Basic device usage:

>>> from bmd_sg.decklink.bmd_decklink import BMDDeckLink, HDRMetadata
>>> device = BMDDeckLink(device_index=0)
>>> device.start()
>>> # Set frame data and output
>>> device.stop()
>>> device.close()

HDR metadata configuration:

>>> metadata = HDRMetadata(eotf=2, max_cll=4000.0, max_fall=400.0)
>>> device.set_hdr_metadata(metadata)

Notes
-----
This module requires the Blackmagic Design Desktop Video drivers and
a compiled libdecklink.dylib library in the same directory.

See Also
--------
bmd_sg.decklink.decklink_types : Type definitions for the SDK wrapper
bmd_sg.decklink_control : High-level device control interface
"""

import ctypes
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from .decklink_types import DecklinkSDKProtocol


class PixelFormatType(Enum):
    """
    Enumeration of supported DeckLink pixel format types.

    This enum defines the various pixel formats supported by DeckLink devices,
    including YUV and RGB formats with different bit depths and packing methods.

    Attributes
    ----------
    FORMAT_8BIT_YUV : str
        8-bit YUV 4:2:2 format ('2vuy')
    FORMAT_10BIT_YUV : str
        10-bit YUV 4:2:2 format ('v210')
    FORMAT_10BIT_YUVA : str
        10-bit YUV with alpha channel ('Ay10')
    FORMAT_8BIT_ARGB : int
        8-bit ARGB format (32)
    FORMAT_8BIT_BGRA : str
        8-bit BGRA format ('BGRA')
    FORMAT_10BIT_RGB : str
        10-bit RGB format ('r210')
    FORMAT_12BIT_RGB : str
        12-bit RGB format, big endian ('R12B')
    FORMAT_12BIT_RGBLE : str
        12-bit RGB format, little endian ('R12L')
    FORMAT_10BIT_RGBXLE : str
        10-bit RGB with padding, little endian ('R10l')
    FORMAT_10BIT_RGBX : str
        10-bit RGB with padding, big endian ('R10b')

    Examples
    --------
    >>> format_type = PixelFormatType.FORMAT_12BIT_RGB
    >>> print(format_type)
    12BIT_RGB
    """

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
        """
        Return a clean string representation of the pixel format.

        Returns
        -------
        str
            The pixel format name without the 'FORMAT_' prefix.
        """
        return f"{self.name[8:]}"


class EOTFType(str, Enum):
    """
    Enumeration of Electro-Optical Transfer Function (EOTF) types.

    This enum defines the standard EOTF types used in HDR video processing,
    corresponding to different gamma curves and dynamic range capabilities.

    Attributes
    ----------
    RESERVED : int
        Reserved value (0)
    SDR : int
        Standard Dynamic Range (1) - Traditional gamma curve
    PQ : int
        Perceptual Quantizer (2) - SMPTE ST 2084 for HDR10
    HLG : int
        Hybrid Log-Gamma (3) - ITU-R BT.2100 for broadcast HDR

    Examples
    --------
    >>> eotf = EOTFType.PQ
    >>> print(eotf)
    2=PQ
    >>> parsed = EOTFType.parse("HLG")
    >>> print(parsed.value)
    3
    """

    RESERVED = ("RESERVED", 0)
    SDR = ("SDR", 1)
    PQ = ("PQ", 2)
    HLG = ("HLG", 3)

    def __new__(cls, value, *args):
        self = str.__new__(cls, value)
        self._value_ = value
        for a in args:
            self._add_value_alias_(a)
        return self

    def __init__(
        self,
        _: str,
        int_value: int,
    ):
        self.int_value = int_value

    def __str__(self):
        """
        Return a formatted string representation of the EOTF type.

        Returns
        -------
        str
            Format: "value=name" (e.g., "2=PQ")
        """
        return f'{self.value}="{self.value}"={self.int_value}'

    @classmethod
    def parse(cls, value):
        """
        Parse an EOTF value from string or integer.

        Parameters
        ----------
        value : str or int
            The EOTF value to parse. Can be an integer (0-3) or
            a string name (case-insensitive).

        Returns
        -------
        EOTFType
            The corresponding EOTF type enum value.

        Raises
        ------
        ValueError
            If the value cannot be parsed as a valid EOTF type.

        Examples
        --------
        >>> EOTFType.parse(2)
        <EOTFType.PQ: 2>
        >>> EOTFType.parse("hlg")
        <EOTFType.HLG: 3>
        """
        # Try integer value - match by int_value
        if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
            int_val = int(value)
            for member in cls:
                if member.int_value == int_val:
                    return member

        # Try string value - match by str_value (case-insensitive)
        if isinstance(value, str):
            str_val = value.upper()
            for member in cls:
                if member.value.upper() == str_val:
                    return member
            # Also try by enum name
            try:
                return cls[str_val]
            except KeyError:
                pass

        # Build error message with valid options
        valid = ", ".join(f"{e.int_value} ({e.value})" for e in cls)
        raise ValueError(f"Invalid EOTF value: {value}. Use one of: {valid}")


# Complete HDR metadata structures (matching C++ implementation)
class ChromaticityCoordinates(ctypes.Structure):
    """
    Chromaticity coordinates for display primaries and white point.

    This structure defines the CIE 1931 chromaticity coordinates for the red,
    green, and blue primaries, as well as the white point of a display or
    color space. Used in HDR metadata to specify color gamut information.

    Parameters
    ----------
    red_xy : tuple[float, float]
        Red primary chromaticity coordinates (x, y)
    green_xy : tuple[float, float]
        Green primary chromaticity coordinates (x, y)
    blue_xy : tuple[float, float]
        Blue primary chromaticity coordinates (x, y)
    white_xy : tuple[float, float]
        White point chromaticity coordinates (x, y)

    Attributes
    ----------
    RedX, RedY : float
        Red primary chromaticity coordinates
    GreenX, GreenY : float
        Green primary chromaticity coordinates
    BlueX, BlueY : float
        Blue primary chromaticity coordinates
    WhiteX, WhiteY : float
        White point chromaticity coordinates

    Examples
    --------
    Create Rec.709 chromaticity coordinates:

    >>> coords = ChromaticityCoordinates(
    ...     red_xy=(0.640, 0.330),
    ...     green_xy=(0.300, 0.600),
    ...     blue_xy=(0.150, 0.060),
    ...     white_xy=(0.3127, 0.3290)
    ... )
    >>> print(f"Red: ({coords.RedX}, {coords.RedY})")
    Red: (0.64, 0.33)

    Notes
    -----
    The chromaticity coordinates are based on the CIE 1931 color space
    and must be within the valid range [0, 1].
    """

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
    red_xy=(0.640, 0.330),  # Rec.709 Red
    green_xy=(0.300, 0.600),  # Rec.709 Green
    blue_xy=(0.150, 0.060),  # Rec.709 Blue
    white_xy=(0.3127, 0.3290),  # D65 White Point
)
"""ChromaticityCoordinates: ITU-R BT.709 color space primaries (standard HD)."""

CHROMATICITYCOORDINATES_REC2020 = ChromaticityCoordinates(
    red_xy=(0.708, 0.292),  # Rec.2020 Red
    green_xy=(0.170, 0.797),  # Rec.2020 Green
    blue_xy=(0.131, 0.046),  # Rec.2020 Blue
    white_xy=(0.3127, 0.3290),  # D65 White Point
)
"""ChromaticityCoordinates: ITU-R BT.2020 color space primaries (ultra HD/HDR)."""

CHROMATICITYCOORDINATES_DCI_P3 = ChromaticityCoordinates(
    red_xy=(0.680, 0.320),  # DCI-P3 Red
    green_xy=(0.265, 0.690),  # DCI-P3 Green
    blue_xy=(0.150, 0.060),  # DCI-P3 Blue
    white_xy=(0.3127, 0.3290),  # D65 White Point (P3-D65)
)
"""ChromaticityCoordinates: DCI-P3 color space primaries (digital cinema)."""

CHROMATICITYCOORDINATES_REC601 = ChromaticityCoordinates(
    red_xy=(0.630, 0.340),  # Rec.601 Red
    green_xy=(0.310, 0.595),  # Rec.601 Green
    blue_xy=(0.155, 0.070),  # Rec.601 Blue
    white_xy=(0.3127, 0.3290),  # D65 White Point
)
"""ChromaticityCoordinates: ITU-R BT.601 color space primaries (standard definition)."""


class HDRMetadata(ctypes.Structure):
    """
    Complete HDR metadata structure for DeckLink output.

    This structure defines comprehensive HDR metadata including EOTF
    (Electro-Optical Transfer Function), display primaries, mastering display
    luminance, and content light levels. Compatible with SMPTE ST 2086 and
    CEA-861.3 HDR metadata standards.

    Parameters
    ----------
    eotf : int, optional
        EOTF type (0=Reserved, 1=SDR, 2=PQ, 3=HLG). Default is 3 (HLG).
    max_display_luminance : float, optional
        Maximum display mastering luminance in cd/m². Default is 1000.0.
    min_display_luminance : float, optional
        Minimum display mastering luminance in cd/m². Default is 0.0001.
    max_cll : float, optional
        Maximum Content Light Level in cd/m². Default is 1000.0.
    max_fall : float, optional
        Maximum Frame Average Light Level in cd/m². Default is 50.0.

    Attributes
    ----------
    EOTF : int
        Electro-Optical Transfer Function type
    referencePrimaries : ChromaticityCoordinates
        Display color primaries and white point
    maxDisplayMasteringLuminance : float
        Maximum mastering display luminance (cd/m²)
    minDisplayMasteringLuminance : float
        Minimum mastering display luminance (cd/m²)
    maxCLL : float
        Maximum Content Light Level (cd/m²)
    maxFALL : float
        Maximum Frame Average Light Level (cd/m²)

    Examples
    --------
    Create HDR metadata with default Rec.2020 primaries:

    >>> metadata = HDRMetadata()
    >>> print(f"EOTF: {metadata.EOTF}")
    EOTF: 3

    Create HDR10 metadata with custom values:

    >>> metadata = HDRMetadata(
    ...     eotf=2,  # PQ
    ...     max_cll=4000.0,
    ...     max_fall=400.0
    ... )
    >>> print(f"Max CLL: {metadata.maxCLL}")
    Max CLL: 4000.0

    Notes
    -----
    The structure automatically sets Rec.2020 color primaries as defaults,
    matching the SignalGenHDR sample implementation from the BMD SDK.

    The EOTF values correspond to:
    - 0: Reserved
    - 1: SDR (traditional gamma)
    - 2: PQ (SMPTE ST 2084, HDR10)
    - 3: HLG (ITU-R BT.2100, broadcast HDR)
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
    """
    Get the DeckLink driver version string.

    Returns
    -------
    str
        The version string of the installed DeckLink driver.

    Examples
    --------
    >>> version = get_decklink_driver_version()
    >>> print(f"Driver version: {version}")
    Driver version: 12.8.1

    Notes
    -----
    Requires DeckLink Desktop Video drivers to be installed.
    """
    return DecklinkSDKWrapper.decklink_get_driver_version().decode("utf-8")


def get_decklink_sdk_version():
    """
    Get the DeckLink SDK version string.

    Returns
    -------
    str
        The version string of the DeckLink SDK library.

    Examples
    --------
    >>> version = get_decklink_sdk_version()
    >>> print(f"SDK version: {version}")
    SDK version: 14.4.0

    Notes
    -----
    This returns the version of the compiled libdecklink.dylib library.
    """
    return DecklinkSDKWrapper.decklink_get_sdk_version().decode("utf-8")


def get_decklink_devices():
    """
    Get list of available DeckLink device names.

    Returns
    -------
    list[str]
        List of device names for all detected DeckLink devices.
        Returns empty list if no devices are found.

    Examples
    --------
    >>> devices = get_decklink_devices()
    >>> print(f"Found {len(devices)} devices")
    Found 2 devices
    >>> for i, device in enumerate(devices):
    ...     print(f"Device {i}: {device}")
    Device 0: DeckLink Mini Monitor 4K
    Device 1: DeckLink Studio 4K

    Notes
    -----
    Devices are returned in the order they are detected by the system.
    The index corresponds to the device_index parameter used in BMDDeckLink.
    """
    count = DecklinkSDKWrapper.decklink_get_device_count()
    devices = []
    for i in range(count):
        name = ctypes.create_string_buffer(256)
        if DecklinkSDKWrapper.decklink_get_device_name_by_index(i, name, 256) == 0:
            devices.append(name.value.decode("utf-8"))
    return devices


class BMDDeckLink:
    """
    RAII wrapper for DeckLink device management.

    This class provides Resource Acquisition Is Initialization (RAII) semantics
    for DeckLink devices, ensuring proper cleanup when the object is destroyed.
    The device is opened on initialization and automatically closed on destruction.

    Parameters
    ----------
    device_index : int, optional
        Index of the DeckLink device to open. Default is 0.

    Attributes
    ----------
    handle : ctypes.c_void_p or None
        Handle to the opened DeckLink device
    device_index : int
        Index of the device that was opened
    _output_started : bool
        Internal flag tracking output state

    Examples
    --------
    Basic usage with automatic cleanup:

    >>> device = BMDDeckLink(device_index=0)
    >>> device.start()
    >>> # Device automatically closed when object goes out of scope

    Manual cleanup if needed:

    >>> device = BMDDeckLink(device_index=0)
    >>> device.start()
    >>> device.close()  # Explicit cleanup

    Raises
    ------
    RuntimeError
        If no DeckLink device is found at the specified index

    Notes
    -----
    The device is automatically closed when the object is destroyed via __del__.
    For guaranteed cleanup timing, use the close() method explicitly.
    """

    def __init__(self, device_index: int = 0):
        self.device_index = device_index
        self.handle = DecklinkSDKWrapper.decklink_open_output_by_index(device_index)
        if not self.handle:
            raise RuntimeError(
                f"No DeckLink output device found at index {device_index}"
            )
        self.started = False

    def __del__(self):
        """Destructor - automatically close device on object destruction."""
        self.close()

    def close(self):
        """
        Close the device and free resources.

        This method is idempotent - it can be called multiple times safely.
        After calling close(), the device cannot be used for further operations.

        Notes
        -----
        This method is automatically called when the object is destroyed.
        """
        if self.handle:
            if self.started:
                DecklinkSDKWrapper.decklink_stop_output(self.handle)
                self.started = False
            DecklinkSDKWrapper.decklink_close(self.handle)
            self.handle = None

    @property
    def is_open(self) -> bool:
        """
        Check if the device is currently open.

        Returns
        -------
        bool
            True if the device is open, False otherwise
        """
        return self.handle is not None

    def start(self):
        """
        Start outputting the color patch.

        Raises
        ------
        RuntimeError
            If the device is not open or if starting output fails
        """
        if not self.handle:
            raise RuntimeError("Device not open")
        if self.started:
            return
        res = DecklinkSDKWrapper.decklink_start_output(self.handle)
        if res != 0:
            raise RuntimeError(f"Failed to start output (error {res})")
        self.started = True

    def stop(self):
        """
        Stop output.

        This method is idempotent - it can be called multiple times safely.
        """
        if not self.handle or not self.started:
            return
        DecklinkSDKWrapper.decklink_stop_output(self.handle)
        self.started = False

    def get_supported_pixel_formats(self):
        """
        Get list of supported pixel format names.

        Returns
        -------
        list[str]
            List of supported pixel format names

        Raises
        ------
        RuntimeError
            If the device is not open
        """
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
        """
        Set the pixel format by index.

        Parameters
        ----------
        format_index : int
            Index of the pixel format to set

        Raises
        ------
        RuntimeError
            If the device is not open or setting the format fails
        """
        if not self.handle:
            raise RuntimeError("Device not open")
        res = DecklinkSDKWrapper.decklink_set_pixel_format(self.handle, format_index)
        if res != 0:
            raise RuntimeError(f"Failed to set pixel format (error {res})")

    def get_pixel_format(self):
        """
        Get the current pixel format index.

        Returns
        -------
        int
            Current pixel format index

        Raises
        ------
        RuntimeError
            If the device is not open
        """
        if not self.handle:
            raise RuntimeError("Device not open")
        return DecklinkSDKWrapper.decklink_get_pixel_format(self.handle)

    def set_frame_eotf(self, eotf=0, maxCLL=0, maxFALL=0):
        """
        Set EOTF metadata for all future frames (legacy method).

        Parameters
        ----------
        eotf : int, optional
            EOTF type. Default is 0.
        maxCLL : int, optional
            Maximum Content Light Level. Default is 0.
        maxFALL : int, optional
            Maximum Frame Average Light Level. Default is 0.

        Raises
        ------
        RuntimeError
            If the device is not open or setting metadata fails
        """
        if not self.handle:
            raise RuntimeError("Device not open")
        res = DecklinkSDKWrapper.decklink_set_eotf_metadata(
            self.handle, eotf, maxCLL, maxFALL
        )
        if res != 0:
            raise RuntimeError(f"Failed to set EOTF metadata (error {res})")

    def set_hdr_metadata(self, metadata):
        """
        Set complete HDR metadata for all future frames.

        Parameters
        ----------
        metadata : HDRMetadata
            HDR metadata structure with complete HDR parameters

        Raises
        ------
        RuntimeError
            If the device is not open or setting metadata fails
        """
        if not self.handle:
            raise RuntimeError("Device not open")
        res = DecklinkSDKWrapper.decklink_set_hdr_metadata(
            self.handle, ctypes.byref(metadata)
        )
        if res != 0:
            raise RuntimeError(f"Failed to set HDR metadata (error {res})")

    def set_frame_data(self, frame_data):
        """
        Set frame data from numpy array.

        Parameters
        ----------
        frame_data : numpy.ndarray
            Frame data with shape (height, width, channels) or (height, width)

        Raises
        ------
        RuntimeError
            If the device is not open or setting frame data fails
        ValueError
            If frame_data is not a valid numpy array
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
        """
        Create a video frame from pending frame data.

        Raises
        ------
        RuntimeError
            If the device is not open or frame creation fails
        """
        if not self.handle:
            raise RuntimeError("Device not open")
        res = DecklinkSDKWrapper.decklink_create_frame_from_data(self.handle)
        if res != 0:
            raise RuntimeError(f"Failed to create frame (error {res})")

    def schedule_frame(self):
        """
        Schedule the current frame for output.

        Raises
        ------
        RuntimeError
            If the device is not open or frame scheduling fails
        """
        if not self.handle:
            raise RuntimeError("Device not open")
        res = DecklinkSDKWrapper.decklink_schedule_frame_for_output(self.handle)
        if res != 0:
            raise RuntimeError(f"Failed to schedule frame (error {res})")

    def start_playback(self):
        """
        Start scheduled playback.

        Raises
        ------
        RuntimeError
            If the device is not open or starting playback fails
        """
        if not self.handle:
            raise RuntimeError("Device not open")
        res = DecklinkSDKWrapper.decklink_start_scheduled_playback(self.handle)
        if res != 0:
            raise RuntimeError(f"Failed to start playback (error {res})")
