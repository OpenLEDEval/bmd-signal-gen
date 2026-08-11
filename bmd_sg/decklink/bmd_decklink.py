#!/usr/bin/env python3
"""
DeckLink device layer for BMD signal generation.

This module exposes DeckLink devices for professional video output through
`pydecklink <https://github.com/Fuse-Technical-Group/pydecklink>`_, the
nanobind-based binding of the Blackmagic Design DeckLink SDK. It supports
HDR metadata, various pixel formats, and comprehensive device management.

The module includes:
- ``DeckLinkOutput`` protocol describing the device output surface
- ``BMDDeckLink`` adapter over ``pydecklink.Device``
- HDR metadata structures with standard color space definitions
- Device enumeration and management
- Frame data handling with numpy integration
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
This module requires the Blackmagic Design Desktop Video drivers.

See Also
--------
bmd_sg.decklink.mock : Mock implementation for development without hardware
"""

import contextlib
from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol, Self, runtime_checkable

import numpy as np
import pydecklink
from pydecklink import packing


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

    # This table is meant to be in line with "Enum BMDPixelFormat" in the
    # DeckLink SDK (DeckLinkAPIModes.h); pydecklink.PixelFormat shares the
    # same fourcc values.
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
        del args  # consumed by __init__ as int_value
        return self

    @classmethod
    def _missing_(cls, value: object) -> "EOTFType | None":
        """
        Resolve ``EOTFType(2)``-style lookups by SDK integer code.

        Replaces the ``_add_value_alias_`` API, which exists only on
        Python 3.13+, so integer lookups work on every supported version.

        Parameters
        ----------
        value : object
            Candidate lookup value; only integers resolve.

        Returns
        -------
        EOTFType or None
            The member whose ``int_value`` matches, or None.
        """
        if isinstance(value, int):
            for member in cls:
                if member.int_value == value:
                    return member
        return None

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


# Complete HDR metadata structures (SMPTE ST 2086 / CTA-861.3)
class GamutChromaticities:
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

    def __init__(
        self,
        red_xy: tuple[float, float],
        green_xy: tuple[float, float],
        blue_xy: tuple[float, float],
        white_xy: tuple[float, float],
    ) -> None:
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


def colorspace_to_gamut_chromaticities(
    colorspace_value: str,
) -> GamutChromaticities:
    """
    Map a ColorSpace enum value string to GamutChromaticities.

    Parameters
    ----------
    colorspace_value : str
        The ColorSpace.value string (e.g., "ITU-R BT.709", "ITU-R BT.2020").

    Returns
    -------
    GamutChromaticities
        The corresponding chromaticity coordinates for HDMI/SDI signaling.

    Notes
    -----
    This function uses the serialized string value from ColorSpace.value
    to enable type-safe mapping from TIFF metadata to DeckLink settings.
    XYZ colorspace maps to Rec.709 as a sensible default.
    """
    mapping = {
        "XYZ": Gamut_Chromaticities_REC709,  # Default for XYZ source
        "ITU-R BT.709": Gamut_Chromaticities_REC709,
        "P3-D65": Gamut_Chromaticities_DCI_P3,
        "ITU-R BT.2020": Gamut_Chromaticities_REC2020,
    }
    if colorspace_value not in mapping:
        # Default to Rec.709 for unknown colorspaces
        return Gamut_Chromaticities_REC709
    return mapping[colorspace_value]


def transfer_function_to_eotf(transfer_value: str) -> "EOTFType":
    """
    Map a TransferFunction enum value string to EOTFType.

    Parameters
    ----------
    transfer_value : str
        The TransferFunction.value string (e.g., "sRGB", "ST.2084").

    Returns
    -------
    EOTFType
        The corresponding EOTF for HDMI/SDI signaling.

    Notes
    -----
    This function uses the serialized string value from TransferFunction.value
    to enable type-safe mapping from TIFF metadata to DeckLink settings.

    SDR transfer functions (linear, sRGB, gamma2.2) all map to SDR EOTF.
    """
    # Map transfer function strings to EOTF types
    # SDR transfers map to SDR EOTF, HDR transfers map to their specific EOTFs
    if transfer_value in ("linear", "sRGB", "gamma2.2"):
        return EOTFType.SDR
    elif transfer_value == "ST.2084":
        return EOTFType.PQ
    elif transfer_value == "HLG":
        return EOTFType.HLG
    else:
        # Default to SDR for unknown transfers
        return EOTFType.SDR


class HDRMetadata:
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

    def __init__(
        self,
        eotf: EOTFType = EOTFType.PQ,
        max_display_luminance: float = 1000.0,
        min_display_luminance: float = 0.0001,
        max_cll: float = 1000.0,
        max_fall: float = 50.0,
    ) -> None:
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


# =============================================================================
# pydecklink bridging
# =============================================================================

# All output uses the synchronous single-frame path at this fixed mode,
# matching the retired C++ wrapper (bmdModeHD1080p30).
DEFAULT_DISPLAY_MODE = pydecklink.DisplayMode.HD1080p30

# RGB formats that require SDI 4:4:4 output, per the SignalGenHDR sample.
# YUV formats use the 4:2:2 default.
_RGB_444_FORMATS = frozenset(
    {
        PixelFormatType.FORMAT_10BIT_RGB,
        PixelFormatType.FORMAT_12BIT_RGB,
        PixelFormatType.FORMAT_12BIT_RGBLE,
        PixelFormatType.FORMAT_10BIT_RGBXLE,
        PixelFormatType.FORMAT_10BIT_RGBX,
        PixelFormatType.FORMAT_8BIT_ARGB,
        PixelFormatType.FORMAT_8BIT_BGRA,
    }
)


def _to_pydecklink_pixel_format(
    pixel_format_type: PixelFormatType,
) -> pydecklink.PixelFormat:
    """
    Convert a PixelFormatType to the pydecklink PixelFormat enum.

    Parameters
    ----------
    pixel_format_type : PixelFormatType
        Pixel format to convert. Its ``sdk_format_code`` is the BMD fourcc
        shared by both enums.

    Returns
    -------
    pydecklink.PixelFormat
        The corresponding pydecklink enum member.

    Raises
    ------
    ValueError
        If the format has no pydecklink equivalent.
    """
    return pydecklink.PixelFormat(pixel_format_type.sdk_format_code)


def _to_pydecklink_hdr_metadata(
    metadata: HDRMetadata,
) -> pydecklink.HDRMetadata:
    """
    Convert an HDRMetadata structure to pydecklink's frame-level metadata.

    Parameters
    ----------
    metadata : HDRMetadata
        Device-level HDR metadata as configured by callers.

    Returns
    -------
    pydecklink.HDRMetadata
        Equivalent metadata for attachment to an output frame. The
        colorspace field keeps pydecklink's Rec.2020 default; the actual
        gamut is carried by the primaries.
    """
    converted = pydecklink.HDRMetadata()
    converted.eotf = pydecklink.EOTF(metadata.EOTF)
    primaries = metadata.referencePrimaries
    converted.red_x = primaries.RedX
    converted.red_y = primaries.RedY
    converted.green_x = primaries.GreenX
    converted.green_y = primaries.GreenY
    converted.blue_x = primaries.BlueX
    converted.blue_y = primaries.BlueY
    converted.white_x = primaries.WhiteX
    converted.white_y = primaries.WhiteY
    converted.max_display_mastering_luminance = metadata.maxDisplayMasteringLuminance
    converted.min_display_mastering_luminance = metadata.minDisplayMasteringLuminance
    converted.max_cll = metadata.maxCLL
    converted.max_fall = metadata.maxFALL
    return converted


def get_decklink_driver_version() -> str:
    """
    Get the DeckLink driver API version string.

    Returns
    -------
    str
        The version string reported by the installed DeckLink driver.

    Examples
    --------
    >>> version = get_decklink_driver_version()
    >>> print(f"Driver version: {version}")
    Driver version: 15.3.1

    Notes
    -----
    Requires DeckLink Desktop Video drivers to be installed.
    """
    return pydecklink.api_version().string


def get_decklink_sdk_version() -> str:
    """
    Get the DeckLink SDK API version string.

    Returns
    -------
    str
        The DeckLink API version reported by the installed driver.
        pydecklink links the SDK dynamically, so the driver's API version
        is the effective SDK version.

    Examples
    --------
    >>> version = get_decklink_sdk_version()
    >>> print(f"SDK version: {version}")
    SDK version: 15.3.1
    """
    return pydecklink.api_version().string


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
    return [info.display_name for info in pydecklink.list_devices()]


@runtime_checkable
class DeckLinkOutput(Protocol):
    """
    Protocol for DeckLink output devices (§spec:decklink-backend).

    Describes the device surface that pattern-output callers depend on.
    ``BMDDeckLink`` satisfies it over real hardware via pydecklink;
    ``MockBMDDeckLink`` satisfies it with no hardware for ``--mock-device``.

    See Also
    --------
    BMDDeckLink : Hardware implementation over pydecklink.Device
    bmd_sg.decklink.mock.MockBMDDeckLink : Hardware-free implementation
    """

    def close(self) -> None:
        """Close the device and free resources. Idempotent."""
        ...

    @property
    def is_open(self) -> bool:
        """Whether the device is currently open."""
        ...

    def start_playback(self) -> None:
        """Start playback output."""
        ...

    def stop_playback(self) -> None:
        """Stop playback output. Idempotent."""
        ...

    def get_supported_pixel_formats(self) -> list[PixelFormatType]:
        """List pixel formats the device supports."""
        ...

    @property
    def supports_hdr(self) -> bool:
        """Whether the device supports HDR metadata output."""
        ...

    def set_hdr_metadata(self, metadata: HDRMetadata) -> None:
        """Set HDR metadata applied to all subsequent frames."""
        ...

    def display_frame(self, frame_data: np.ndarray) -> None:
        """Display a single frame synchronously."""
        ...


class BMDDeckLink:
    """
    DeckLink output device adapter over pydecklink.

    This class provides Resource Acquisition Is Initialization (RAII)
    semantics for DeckLink devices, ensuring proper cleanup when the object
    is destroyed. The device is opened on initialization and automatically
    closed on destruction. It satisfies the ``DeckLinkOutput`` protocol.

    Parameters
    ----------
    device_index : int, optional
        Index of the DeckLink device to open. Default is 0.

    Attributes
    ----------
    device_index : int
        Index of the device that was opened
    started : bool
        Whether playback output is currently enabled

    Examples
    --------
    Context manager usage (recommended):

    >>> with BMDDeckLink(device_index=0) as device:
    ...     device.start_playback()
    ...     # Device automatically closed when exiting the with block

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
    HDR metadata is stored device-level and attached to every frame this
    adapter builds, because the SDK (and pydecklink) carry HDR10 metadata
    per frame. Callers keep the simpler device-level model.

    Output uses the synchronous single-frame path at HD 1080p30
    (``DEFAULT_DISPLAY_MODE``), matching the retired C++ wrapper.
    """

    def __init__(self, device_index: int = 0) -> None:
        self.device_index = device_index
        # Assigned before Device construction so __del__ is safe if it raises.
        self._device: pydecklink.Device | None = None
        try:
            self._device = pydecklink.Device(device_index)
        except (IndexError, RuntimeError) as error:
            raise RuntimeError(
                f"No DeckLink output device found at index {device_index}"
            ) from error
        self.started = False
        # Defaults match the retired C++ wrapper (bmdFormat12BitRGBLE, no
        # HDR metadata until explicitly set).
        self._pixel_format = PixelFormatType.FORMAT_12BIT_RGBLE
        self._hdr_metadata: HDRMetadata | None = None

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
        if self._device is not None:
            if self.started:
                self.stop_playback()
            self._device = None

    @property
    def is_open(self) -> bool:
        """
        Check if the device is currently open.

        Returns
        -------
        bool
            True if the device is open, False otherwise
        """
        return self._device is not None

    def _require_device(self) -> pydecklink.Device:
        """
        Return the open pydecklink device or raise.

        Returns
        -------
        pydecklink.Device
            The open device handle.

        Raises
        ------
        RuntimeError
            If the device is not open.
        """
        if self._device is None:
            raise RuntimeError("Device not open")
        return self._device

    def start_playback(self) -> None:
        """
        Start playback output to the DeckLink device.

        Configures SDI 4:4:4 output for RGB pixel formats (following the
        BMD SignalGenHDR sample), then enables video output at
        ``DEFAULT_DISPLAY_MODE``.

        Raises
        ------
        RuntimeError
            If the device is not open or if starting playback fails
        """
        device = self._require_device()
        if self.started:
            return
        # Best-effort: devices without SDI output (e.g. HDMI-only) reject
        # this flag; output still works at their default.
        with contextlib.suppress(RuntimeError):
            device.set_config_flag(
                pydecklink.ConfigurationID.Config444SDIVideoOutput,
                self._pixel_format in _RGB_444_FORMATS,
            )
        try:
            device.enable_video_output(DEFAULT_DISPLAY_MODE)
        except RuntimeError as error:
            raise RuntimeError(f"Failed to start playback output ({error})") from error
        self.started = True

    def stop_playback(self) -> None:
        """
        Stop playback output from the DeckLink device.

        This method is idempotent - it can be called multiple times safely.
        """
        if self._device is None or not self.started:
            return
        self._device.disable_video_output()
        self.started = False

    def get_supported_pixel_formats(self) -> list[PixelFormatType]:
        """
        Get list of supported pixel format enum values.

        Queries the device for each known format at ``DEFAULT_DISPLAY_MODE``.

        Returns
        -------
        list[PixelFormatType]
            List of supported pixel format enum values

        Raises
        ------
        RuntimeError
            If the device is not open
        """
        device = self._require_device()
        supported = []
        for pixel_format_type in PixelFormatType:
            if pixel_format_type.sdk_format_code == 0:
                continue
            try:
                pd_format = _to_pydecklink_pixel_format(pixel_format_type)
            except ValueError:
                # Format known to this project but not bound by pydecklink
                continue
            if device.does_support_video_mode(
                pydecklink.VideoConnection.Unspecified,
                DEFAULT_DISPLAY_MODE,
                pd_format,
            ):
                supported.append(pixel_format_type)
        return supported

    @property
    def supports_hdr(self) -> bool:
        """
        Check if the device supports HDR metadata output.

        Returns
        -------
        bool
            True if the device supports HDR metadata, False otherwise

        Raises
        ------
        RuntimeError
            If the device is not open
        """
        return bool(self._require_device().supports_hdr)

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
        """
        self._require_device()
        return self._pixel_format

    @pixel_format.setter
    def pixel_format(self, pixel_format_type: PixelFormatType) -> None:
        """
        Set the pixel format using a PixelFormatType enum.

        The format takes effect when playback starts; frames are packed to
        this format by ``display_frame``.

        Parameters
        ----------
        pixel_format_type : PixelFormatType
            The pixel format enum to set

        Raises
        ------
        RuntimeError
            If the device is not open or the device does not support the
            format
        """
        device = self._require_device()
        try:
            pd_format = _to_pydecklink_pixel_format(pixel_format_type)
        except ValueError as error:
            raise RuntimeError(
                f"Failed to set pixel format {pixel_format_type.name} ({error})"
            ) from error
        if not device.does_support_video_mode(
            pydecklink.VideoConnection.Unspecified,
            DEFAULT_DISPLAY_MODE,
            pd_format,
        ):
            raise RuntimeError(
                f"Failed to set pixel format {pixel_format_type.name} "
                "(not supported by device)"
            )
        self._pixel_format = pixel_format_type

    def set_hdr_metadata(self, metadata: HDRMetadata) -> None:
        """
        Set complete HDR metadata for all future frames.

        The metadata is attached to every frame built by ``display_frame``
        (the SDK carries HDR10 metadata per frame).

        Parameters
        ----------
        metadata : HDRMetadata
            HDR metadata structure with complete HDR parameters

        Raises
        ------
        RuntimeError
            If the device is not open
        """
        self._require_device()
        self._hdr_metadata = metadata

    def display_frame(self, frame_data: np.ndarray) -> None:
        """
        Display a single frame synchronously.

        Packs the frame to the configured pixel format, attaches any HDR
        metadata, and displays it via the synchronous single-frame path.

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
        device = self._require_device()
        if not isinstance(frame_data, np.ndarray):
            raise ValueError("frame_data must be a numpy array")
        if frame_data.ndim == 2:
            frame_data = np.stack([frame_data] * 3, axis=-1)
        elif frame_data.ndim != 3:
            raise ValueError("frame_data must be 2D or 3D array")
        frame_data = np.ascontiguousarray(frame_data.astype(np.uint16))
        height, width = frame_data.shape[:2]

        pd_format = _to_pydecklink_pixel_format(self._pixel_format)
        try:
            row_bytes = pydecklink.get_row_bytes(pd_format, width)
            frame = device.create_video_frame(width, height, row_bytes, pd_format)
            frame.data[:] = packing.pack(frame_data, pd_format, frame.row_bytes)
            if self._hdr_metadata is not None:
                frame.set_hdr_metadata(_to_pydecklink_hdr_metadata(self._hdr_metadata))
            device.display_frame_sync_frame(frame)
        except RuntimeError as error:
            raise RuntimeError(f"Failed to display frame ({error})") from error
