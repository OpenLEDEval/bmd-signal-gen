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
- Unified DecklinkSettings configuration class

Examples
--------
Basic device usage:

>>> from bmd_sg.decklink.bmd_decklink import BMDDeckLink, HDRMetadata
>>> device = BMDDeckLink(device_index=0)
>>> device.start_playback()
>>> # Set frame data and output
>>> device.stop_playback()
>>> device.close()

HDR metadata configuration:

>>> metadata = HDRMetadata(eotf=2, max_cll=4000.0, max_fall=400.0)
>>> device.set_hdr_metadata(metadata)

Unified settings configuration:

>>> settings = DecklinkSettings(device=0, width=1920, height=1080)
>>> # Use settings to configure device

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
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar, Self

import numpy as np


class PixelFormatType(str, Enum):
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

    # This table is meant to be in line with "Enum BMDPixelFormat" in
    # cpp/Blackmagic DeckLink SDK 14.4/Mac/include/DeckLinkAPIModes.h
    # TODO: Add field to indicate library support
    # TODO: Add human readable primary selections string and fall back on BMD
    # string in case the human readable string isn't set. Ensure parse can refer
    # to either the human readable or bmd string, as well as handling both as a
    # value alias.

    FORMAT_UNSPECIFIED = ("unkn", 8, 0)
    FORMAT_8BIT_YUV = ("2vuy", 8, 0x32767579)
    FORMAT_10BIT_YUV = ("v210", 10, 0x76323130)
    FORMAT_10BIT_YUVA = ("Ay10", 10, 0x41793130)
    FORMAT_8BIT_ARGB = ("32", 8, 32)
    FORMAT_8BIT_BGRA = ("BGRA", 8, 0x42475241)
    FORMAT_10BIT_RGB = ("r210", 10, 0x72323130)
    FORMAT_12BIT_RGB = ("R12B", 12, 0x52313242)
    FORMAT_12BIT_RGBLE = ("R12L", 12, 0x5231324C)
    FORMAT_10BIT_RGBXLE = ("R10l", 10, 0x5231306C)
    FORMAT_10BIT_RGBX = ("R10b", 10, 0x52313062)

    FORMAT_H265 = ("hev1", 8, 0x68657631)
    FORMAT_DNxHR = ("AVdh", 8, 0x41566468)

    def __new__(cls, value: str, *_: Any):
        self = str.__new__(cls, value)
        self._value_ = value
        return self

    def __init__(self, value: str, bit_depth: int, sdk_format_code: int):  # noqa: ARG002
        self.bit_depth = bit_depth
        self.sdk_format_code = sdk_format_code

    def __str__(self) -> str:
        """
        Return a clean string representation of the pixel format.

        Returns
        -------
        str
            The pixel format name without the 'FORMAT_' prefix.
        """
        return f"{self.name[8:]}"

    @classmethod
    def parse(cls, value: str | int) -> Self:
        """
        Parse a pixel format string or SDK format code and return the corresponding enum member.

        This method attempts to match the input against pixel format values, enum names
        (case-insensitive), or SDK format codes. It supports all three identification methods
        for maximum flexibility.

        Parameters
        ----------
        value : str or int
            The pixel format identifier to parse. Can be:
            - Format code string (e.g., 'R12L', '2vuy', 'BGRA')
            - Enum name (e.g., 'FORMAT_12BIT_RGBLE' or '12BIT_RGBLE')
            - SDK format code integer (e.g., 0x5231324C for R12L)

        Returns
        -------
        PixelFormatType
            The matching pixel format enum member.

        Raises
        ------
        ValueError
            If the pixel format identifier cannot be parsed or matched to any
            known format.

        Examples
        --------
        Parse by format code string:

        >>> fmt = PixelFormatType.parse('R12L')
        >>> print(fmt)
        12BIT_RGBLE

        Parse by enum name:

        >>> fmt = PixelFormatType.parse('FORMAT_10BIT_RGB')
        >>> print(fmt)
        10BIT_RGB

        Parse by SDK format code:

        >>> fmt = PixelFormatType.parse(0x5231324C)
        >>> print(fmt)
        12BIT_RGBLE

        Parse by shortened name:

        >>> fmt = PixelFormatType.parse('10BIT_RGB')
        >>> print(fmt)
        10BIT_RGB

        Notes
        -----
        This method performs case-insensitive matching for strings and will attempt to
        match against format values, enum names, and SDK format codes.
        """
        # Handle SDK format code (integer)
        if isinstance(value, int):
            for member in cls:
                if member.sdk_format_code == value:
                    return member

            # Build error message with valid SDK codes
            sdk_codes = ", ".join(f"0x{member.sdk_format_code:08X}" for member in cls)
            raise ValueError(
                f"Invalid SDK format code: 0x{value:08X}. Valid SDK codes: {sdk_codes}"
            )

        # Handle string values
        if not isinstance(value, str):
            raise ValueError(
                f"Expected string or int, got {type(value).__name__}: {value}"
            )

        value_upper = value.upper().strip()

        # Try matching by format value (e.g., 'R12L', '2vuy', 'BGRA')
        for member in cls:
            if member.value.upper() == value_upper:
                return member

        # Try matching by enum name with or without FORMAT_ prefix
        # Handle both 'FORMAT_12BIT_RGB' and '12BIT_RGB'
        if not value_upper.startswith("FORMAT_"):
            value_upper = f"FORMAT_{value_upper}"

        try:
            return cls[value_upper]
        except KeyError:
            pass

        # Build error message with valid options
        format_codes = ", ".join(f"'{member.value}'" for member in cls)
        enum_names = ", ".join(member.name for member in cls)
        sdk_codes = ", ".join(f"0x{member.sdk_format_code:08X}" for member in cls)
        raise ValueError(
            f"Invalid pixel format: '{value}'. "
            f"Valid format codes: {format_codes}. "
            f"Valid enum names: {enum_names}. "
            f"Valid SDK codes: {sdk_codes}"
        )


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

    def __new__(cls, value: str, *args: Any):
        self = str.__new__(cls, value)
        self._value_ = value
        for a in args:
            self._add_value_alias_(a)  # type: ignore Added in python 3.13
        return self

    def __init__(
        self,
        _: str,
        int_value: int,
    ):
        self.int_value = int_value

    def __str__(self) -> str:
        """
        Return a formatted string representation of the EOTF type.

        Returns
        -------
        str
            Format: "value=name" (e.g., "2=PQ")
        """
        return f'{self.value}="{self.value}"={self.int_value}'

    @classmethod
    def parse(cls, value: str | int) -> Self:
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
class GamutChromaticities(ctypes.Structure):
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

    >>> coords = Gamut_Chromaticities(
    ...     red_xy=(0.640, 0.330),
    ...     green_xy=(0.300, 0.600),
    ...     blue_xy=(0.150, 0.060),
    ...     white_xy=D65_WHITE_POINT
    ... )
    >>> print(f"Red: ({coords.RedX}, {coords.RedY})")
    Red: (0.64, 0.33)

    Notes
    -----
    The chromaticity coordinates are based on the CIE 1931 color space
    and must be within the valid range [0, 1].
    """

    _fields_: ClassVar = [
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
    ) -> None:
        super().__init__()
        self.RedX = red_xy[0]
        self.RedY = red_xy[1]
        self.GreenX = green_xy[0]
        self.GreenY = green_xy[1]
        self.BlueX = blue_xy[0]
        self.BlueY = blue_xy[1]
        self.WhiteX = white_xy[0]
        self.WhiteY = white_xy[1]


# D65 white point (CIE 1931) - Standard illuminant
D65_WHITE_POINT = (0.3127, 0.3290)

# Standard chromaticity coordinates for common color spaces
Gamut_Chromaticities_REC709 = GamutChromaticities(
    red_xy=(0.640, 0.330),  # Rec.709 Red
    green_xy=(0.300, 0.600),  # Rec.709 Green
    blue_xy=(0.150, 0.060),  # Rec.709 Blue
    white_xy=D65_WHITE_POINT,  # D65 White Point
)
"""Gamut_Chromaticities: ITU-R BT.709 color space primaries (standard HD)."""

Gamut_Chromaticities_REC2020 = GamutChromaticities(
    red_xy=(0.708, 0.292),  # Rec.2020 Red
    green_xy=(0.170, 0.797),  # Rec.2020 Green
    blue_xy=(0.131, 0.046),  # Rec.2020 Blue
    white_xy=D65_WHITE_POINT,  # D65 White Point
)
"""Gamut_Chromaticities: ITU-R BT.2020 color space primaries (ultra HD/HDR)."""

Gamut_Chromaticities_DCI_P3 = GamutChromaticities(
    red_xy=(0.680, 0.320),  # DCI-P3 Red
    green_xy=(0.265, 0.690),  # DCI-P3 Green
    blue_xy=(0.150, 0.060),  # DCI-P3 Blue
    white_xy=D65_WHITE_POINT,  # D65 White Point (P3-D65)
)
"""Gamut_Chromaticities: DCI-P3 color space primaries (digital cinema)."""

GAMUT_CHROMATICITIES_REC601 = GamutChromaticities(
    red_xy=(0.630, 0.340),  # Rec.601 Red
    green_xy=(0.310, 0.595),  # Rec.601 Green
    blue_xy=(0.155, 0.070),  # Rec.601 Blue
    white_xy=D65_WHITE_POINT,  # D65 White Point
)
"""Gamut_Chromaticities: ITU-R BT.601 color space primaries (standard definition)."""


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
    referencePrimaries : Gamut_Chromaticities
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

    _fields_: ClassVar = [
        ("EOTF", ctypes.c_int64),
        ("referencePrimaries", GamutChromaticities),
        ("maxDisplayMasteringLuminance", ctypes.c_double),
        ("minDisplayMasteringLuminance", ctypes.c_double),
        ("maxCLL", ctypes.c_double),
        ("maxFALL", ctypes.c_double),
    ]

    def __init__(
        self,
        eotf: EOTFType = EOTFType.PQ,
        max_display_luminance: float = 1000.0,
        min_display_luminance: float = 0.0001,
        max_cll: float = 1000.0,
        max_fall: float = 50.0,
    ) -> None:
        super().__init__()
        self.EOTF = eotf.int_value
        self.maxDisplayMasteringLuminance = max_display_luminance
        self.minDisplayMasteringLuminance = min_display_luminance
        self.maxCLL = max_cll
        self.maxFALL = max_fall

        # Set default Rec2020 primaries (matching C++ defaults)
        self.referencePrimaries = Gamut_Chromaticities_REC2020


# Video resolution constants for standard formats
DEFAULT_WIDTH = 1920  # Full HD/4K width
DEFAULT_HEIGHT = 1080  # Full HD height

# HDR metadata constants following industry standards
DEFAULT_MAX_CLL = 10000.0  # Maximum Content Light Level (cd/m²)
DEFAULT_MAX_FALL = 400.0  # Maximum Frame Average Light Level (cd/m²)
DEFAULT_MAX_DISPLAY_MASTERING_LUMINANCE = 1000.0  # Display mastering luminance (cd/m²)
DEFAULT_MIN_DISPLAY_MASTERING_LUMINANCE = 0.0001  # Minimum display luminance (cd/m²)


@dataclass
class DecklinkSettings:
    """
    Comprehensive configuration settings for DeckLink device initialization and operation.

    This dataclass consolidates all settings required for configuring a DeckLink device
    including device selection, video resolution, pixel format, region of interest,
    HDR metadata parameters, and color space information. It provides a unified
    interface for all DeckLink-related configuration.

    Parameters
    ----------
    device : int, optional
        Index of the DeckLink device to use. Default is 0.
    pixel_format : PixelFormatType | None, optional
        Pixel format enum, None for auto-selection. Default is None.
    width : int, optional
        Frame width in pixels. Default is 1920.
    height : int, optional
        Frame height in pixels. Default is 1080.
    roi_x : int, optional
        Region of interest X offset. Default is 0.
    roi_y : int, optional
        Region of interest Y offset. Default is 0.
    roi_width : int, optional
        Region of interest width. Default is 1920.
    roi_height : int, optional
        Region of interest height. Default is 1080.
    no_hdr : bool, optional
        Whether to disable HDR metadata output. Default is False.
    eotf : EOTFType, optional
        Electro-Optical Transfer Function type. Default is PQ (HDR10).
    max_cll : float, optional
        Maximum Content Light Level in cd/m². Default is 10000.0.
    max_fall : float, optional
        Maximum Frame Average Light Level in cd/m². Default is 400.0.
    max_display_mastering_luminance : float, optional
        Maximum display mastering luminance in cd/m². Default is 1000.0.
    min_display_mastering_luminance : float, optional
        Minimum display mastering luminance in cd/m². Default is 0.0001.
    gamut_chromaticities : Gamut_Chromaticities, optional
        Complete color gamut definition including red, green, blue primaries
        and white point chromaticity coordinates. Default is Rec.2020.

    Attributes
    ----------
    device : int
        Index of the DeckLink device to use
    pixel_format : PixelFormatType | None
        Pixel format enum, None for auto-selection
    width : int
        Frame width in pixels
    height : int
        Frame height in pixels
    roi_x : int
        Region of interest X offset
    roi_y : int
        Region of interest Y offset
    roi_width : int
        Region of interest width
    roi_height : int
        Region of interest height
    no_hdr : bool
        Whether to disable HDR metadata output
    eotf : EOTFType
        Electro-Optical Transfer Function type
    max_cll : float
        Maximum Content Light Level in cd/m²
    max_fall : float
        Maximum Frame Average Light Level in cd/m²
    max_display_mastering_luminance : float
        Maximum display mastering luminance in cd/m²
    min_display_mastering_luminance : float
        Minimum display mastering luminance in cd/m²
    gamut_chromaticities : Gamut_Chromaticities
        Complete color gamut definition including red, green, blue primaries
        and white point chromaticity coordinates

    Examples
    --------
    Create settings with defaults:

    >>> settings = DecklinkSettings()
    >>> print(f"Device: {settings.device}, Resolution: {settings.width}x{settings.height}")
    Device: 0, Resolution: 1920x1080

    Create settings for specific device with custom HDR:

    >>> settings = DecklinkSettings(
    ...     device=1,
    ...     width=3840,
    ...     height=2160,
    ...     eotf=EOTFType.HLG,
    ...     max_cll=4000.0
    ... )
    >>> print(f"EOTF: {settings.eotf}, Max CLL: {settings.max_cll}")
    EOTF: HLG, Max CLL: 4000.0

    Create settings with custom ROI:

    >>> settings = DecklinkSettings(
    ...     roi_x=100,
    ...     roi_y=100,
    ...     roi_width=1720,
    ...     roi_height=880
    ... )
    >>> print(f"ROI: {settings.roi_x},{settings.roi_y} {settings.roi_width}x{settings.roi_height}")
    ROI: 100,100 1720x880

    Notes
    -----
    This class consolidates all DeckLink device configuration into a single
    interface, eliminating the need for multiple settings classes and conversion
    functions. It supports complete HDR metadata configuration following
    industry standards (SMPTE ST 2086, CEA-861.3).

    The default color primaries are set to Rec.2020 (ITU-R BT.2020) which is
    the standard for Ultra HD and HDR content. The default EOTF is PQ
    (Perceptual Quantizer) as specified in SMPTE ST 2084 for HDR10.

    See Also
    --------
    HDRMetadata : HDR metadata structure for device configuration
    PixelFormatType : Available pixel format options
    EOTFType : Electro-Optical Transfer Function types
    """

    # Device parameters
    device: int = 0
    pixel_format: PixelFormatType | None = None
    width: int = DEFAULT_WIDTH
    height: int = DEFAULT_HEIGHT

    # ROI parameters
    roi_x: int = 0
    roi_y: int = 0
    roi_width: int = DEFAULT_WIDTH
    roi_height: int = DEFAULT_HEIGHT

    # HDR metadata settings
    no_hdr: bool = False
    eotf: EOTFType = EOTFType.PQ
    max_cll: float = DEFAULT_MAX_CLL
    max_fall: float = DEFAULT_MAX_FALL
    max_display_mastering_luminance: float = DEFAULT_MAX_DISPLAY_MASTERING_LUMINANCE
    min_display_mastering_luminance: float = DEFAULT_MIN_DISPLAY_MASTERING_LUMINANCE

    # Color space primaries and white point
    gamut_chromaticities: GamutChromaticities = Gamut_Chromaticities_REC2020


def _configure_function_signatures(lib: ctypes.CDLL) -> None:  # noqa: C901
    """Configure ctypes function signatures for all DeckLink SDK functions.

    Sets up argument types and return types for all C functions in the DeckLink
    SDK library to ensure proper type safety and memory management when calling
    from Python.

    Parameters
    ----------
    lib : ctypes.CDLL
        The loaded DeckLink SDK library instance.

    Notes
    -----
    This function configures signatures for:
    - Device enumeration (count, names)
    - Device management (open, close, start, stop)
    - Pixel format management
    - HDR metadata handling
    - Frame data operations
    - Version information
    """

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

    if hasattr(lib, "decklink_start_output_with_mode"):
        lib.decklink_start_output_with_mode.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
        ]
        lib.decklink_start_output_with_mode.restype = ctypes.c_int

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
            ctypes.c_uint32,
        ]
        lib.decklink_set_pixel_format.restype = ctypes.c_int

    if hasattr(lib, "decklink_get_pixel_format"):
        lib.decklink_get_pixel_format.argtypes = [ctypes.c_void_p]
        lib.decklink_get_pixel_format.restype = ctypes.c_uint32

    # HDR metadata functions
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

    # Synchronous display function
    if hasattr(lib, "decklink_display_frame_sync"):
        lib.decklink_display_frame_sync.argtypes = [ctypes.c_void_p]
        lib.decklink_display_frame_sync.restype = ctypes.c_int

    # HDR capability detection functions
    if hasattr(lib, "decklink_device_supports_hdr"):
        lib.decklink_device_supports_hdr.argtypes = [ctypes.c_void_p]
        lib.decklink_device_supports_hdr.restype = ctypes.c_bool

    # Version info functions
    if hasattr(lib, "decklink_get_driver_version"):
        lib.decklink_get_driver_version.argtypes = []
        lib.decklink_get_driver_version.restype = ctypes.c_char_p

    if hasattr(lib, "decklink_get_sdk_version"):
        lib.decklink_get_sdk_version.argtypes = []
        lib.decklink_get_sdk_version.restype = ctypes.c_char_p


def _try_load_decklink_sdk() -> ctypes.CDLL:
    """Load the DeckLink SDK library and configure function signatures.

    Attempts to load the compiled libdecklink.dylib from the same directory
    as this Python module, then configures all ctypes function signatures
    for type safety.

    Returns
    -------
    ctypes.CDLL
        The loaded and configured DeckLink SDK library instance.

    Raises
    ------
    FileNotFoundError
        If libdecklink.dylib cannot be found in the expected location.
    OSError
        If the library exists but cannot be loaded (e.g., architecture mismatch,
        missing dependencies, or permission issues).

    Notes
    -----
    The library file must be built from the C++ source in the cpp/ directory
    and placed in the same directory as this module.
    """
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

    return decklink_lib


DecklinkSDKWrapper: ctypes.CDLL = _try_load_decklink_sdk()


def get_decklink_driver_version() -> str:
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


def get_decklink_sdk_version() -> str:
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


def ndarray_to_bmd_frame_buffer(
    frame_data: np.ndarray,
) -> tuple[Any, int, int]:
    """
    Convert numpy array to BMD-compatible frame buffer.

    Parameters
    ----------
    frame_data : numpy.ndarray
        Frame data with shape (height, width, channels) or (height, width)

    Returns
    -------
    tuple[ctypes.POINTER(ctypes.c_uint16), int, int]
        Tuple containing (data_ptr, width, height)

    Raises
    ------
    ValueError
        If frame_data is not a valid numpy array or has invalid dimensions
    """
    if not isinstance(frame_data, np.ndarray):
        raise ValueError("frame_data must be a numpy array")

    # Get dimensions
    if frame_data.ndim == 2:
        height, width = frame_data.shape
    elif frame_data.ndim == 3:
        height, width, _ = frame_data.shape
    else:
        raise ValueError("frame_data must be 2D or 3D array")

    # Note: frame_data should already be uint16 and contiguous
    # These conversions are handled in display_frame() before calling this function

    # Get pointer to data
    data_ptr = frame_data.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16))
    return data_ptr, height, width


def get_decklink_devices() -> list[str]:
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
    Context manager usage (recommended):

    >>> with BMDDeckLink(device_index=0) as device:
    ...     device.start_playback()
    ...     # Device automatically closed when exiting the with block

    Basic usage with automatic cleanup:

    >>> device = BMDDeckLink(device_index=0)
    >>> device.start_playback()
    >>> # Device automatically closed when object goes out of scope

    Manual cleanup if needed:

    >>> device = BMDDeckLink(device_index=0)
    >>> device.start_playback()
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

    def __init__(self, device_index: int = 0) -> None:
        self.device_index = device_index
        self.handle = DecklinkSDKWrapper.decklink_open_output_by_index(device_index)
        if not self.handle:
            raise RuntimeError(
                f"No DeckLink output device found at index {device_index}"
            )
        self.started = False

    def __del__(self) -> None:
        """Destructor - automatically close device on object destruction."""
        self.close()

    def __enter__(self) -> Self:
        """
        Enter the context manager.

        Returns
        -------
        Self
            The BMDDeckLink instance for use in the with statement

        Examples
        --------
        >>> with BMDDeckLink(0) as device:
        ...     device.start_playback()
        ...     # Device automatically closed when exiting the with block
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any | None,
    ) -> None:
        """
        Exit the context manager and close the device.

        Parameters
        ----------
        exc_type : type[BaseException] | None
            Exception type if an exception occurred, None otherwise
        exc_val : BaseException | None
            Exception value if an exception occurred, None otherwise
        exc_tb : Any | None
            Exception traceback if an exception occurred, None otherwise

        Notes
        -----
        The device is automatically closed regardless of whether an exception
        occurred within the with block.
        """
        self.close()

    def close(self) -> None:
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
                self.stop_playback()
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

    def start_playback(self) -> None:
        """
        Start playback output to the DeckLink device.

        Raises
        ------
        RuntimeError
            If the device is not open or if starting playback fails
        """
        if not self.handle:
            raise RuntimeError("Device not open")
        if self.started:
            return
        res = DecklinkSDKWrapper.decklink_start_output(self.handle)
        if res != 0:
            raise RuntimeError(f"Failed to start playback output (error {res})")
        self.started = True

    def stop_playback(self) -> None:
        """
        Stop playback output from the DeckLink device.

        This method is idempotent - it can be called multiple times safely.
        """
        if not self.handle or not self.started:
            return
        DecklinkSDKWrapper.decklink_stop_output(self.handle)
        self.started = False

    def get_supported_pixel_formats(self) -> list[PixelFormatType]:
        """
        Get list of supported pixel format enum values.

        Returns
        -------
        list[PixelFormatType]
            List of supported pixel format enum values

        Raises
        ------
        RuntimeError
            If the device is not open

        Notes
        -----
        If a pixel format string cannot be parsed to a known enum value, a warning
        is printed asking the user to report the unknown format as a GitHub issue.
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
                format_string = name.value.decode("utf-8")
                try:
                    # Try to parse the format string to a PixelFormatType enum
                    # First try direct parsing, then try extracting format codes from parentheses
                    try:
                        pixel_format = PixelFormatType.parse(format_string)
                    except ValueError as e:
                        # Try to extract format code from strings like "8Bit ARGB (32)" or "12Bit RGB LE ('R12L')"
                        # Look for format codes in parentheses, both with and without quotes
                        match = re.search(r"\((?:'([^']+)'|([^)]+))\)", format_string)
                        if match:
                            format_code = match.group(1) or match.group(2)
                            pixel_format = PixelFormatType.parse(format_code)
                        else:
                            raise ValueError(
                                f"Could not extract format code from: {format_string}"
                            ) from e

                    formats.append(pixel_format)
                except ValueError:
                    # Print warning and ask user to report unknown format
                    print(
                        f"⚠️  WARNING: Unknown pixel format detected: '{format_string}'"
                    )
                    print(
                        "📝 Please help improve this project by reporting this unknown format:"
                    )
                    print(f"   1. Copy this exact string: '{format_string}'")
                    print(
                        "   2. Create a new issue at: https://github.com/OpenLEDEval/bmd-signal-gen/issues"
                    )
                    print(
                        "   3. Include your device model and the unknown format string"
                    )
                    print("   This format will be skipped for now.")
                    print()
        return formats

    @property
    def supports_hdr(self) -> bool:
        return DecklinkSDKWrapper.decklink_device_supports_hdr(self.handle)

    @property
    def pixel_format(self) -> PixelFormatType:
        """
        Get the current pixel format as a PixelFormatType enum.

        Returns
        -------
        PixelFormatType
            Current pixel format enum value

        Raises
        ------
        RuntimeError
            If the device is not open
        ValueError
            If the SDK format code cannot be matched to a known PixelFormatType
        """
        if not self.handle:
            raise RuntimeError("Device not open")
        sdk_format_code = DecklinkSDKWrapper.decklink_get_pixel_format(self.handle)
        return PixelFormatType.parse(sdk_format_code)

    @pixel_format.setter
    def pixel_format(self, pixel_format_type: PixelFormatType) -> None:
        """
        Set the pixel format using a PixelFormatType enum.

        Parameters
        ----------
        pixel_format_type : PixelFormatType
            The pixel format enum to set

        Raises
        ------
        RuntimeError
            If the device is not open or setting the format fails
        """
        if not self.handle:
            raise RuntimeError("Device not open")
        res = DecklinkSDKWrapper.decklink_set_pixel_format(
            self.handle, pixel_format_type.sdk_format_code
        )
        if res != 0:
            raise RuntimeError(
                f"Failed to set pixel format {pixel_format_type.name} (error {res})"
            )

    def set_hdr_metadata(self, metadata: HDRMetadata) -> None:
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

    def display_frame(self, frame_data: np.ndarray) -> None:
        """
        Display a single frame synchronously.

        Parameters
        ----------
        frame_data : numpy.ndarray
            Frame data with shape (height, width, channels) or (height, width)

        Raises
        ------
        RuntimeError
            If the device is not open or any frame operation fails
        ValueError
            If frame_data is not a valid numpy array
        """
        if not self.handle:
            raise RuntimeError("Device not open")

        frame_data = np.astype(frame_data, np.uint16, copy=True)
        frame_data = np.ascontiguousarray(frame_data)

        # Set frame data
        data_ptr, height, width = ndarray_to_bmd_frame_buffer(frame_data)
        res = DecklinkSDKWrapper.decklink_set_frame_data(
            self.handle, data_ptr, width, height
        )
        if res != 0:
            raise RuntimeError(f"Failed to set frame data (error {res})")

        # Create frame
        res = DecklinkSDKWrapper.decklink_create_frame_from_data(self.handle)
        if res != 0:
            raise RuntimeError(f"Failed to create frame (error {res})")

        # Display frame synchronously
        res = DecklinkSDKWrapper.decklink_display_frame_sync(self.handle)
        if res != 0:
            raise RuntimeError(f"Failed to display frame synchronously (error {res})")
