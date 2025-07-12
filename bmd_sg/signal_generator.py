"""
Signal generator configuration and settings.

This module provides dataclasses and constants for configuring BMD signal
generation including video resolution, HDR metadata, and color space settings.
"""

from dataclasses import dataclass, field

from bmd_sg.decklink.bmd_decklink import EOTFType

# Video resolution constants for standard formats
DEFAULT_WIDTH = 1920  # Full HD/4K width
DEFAULT_HEIGHT = 1080  # Full HD height

# HDR metadata constants following industry standards
DEFAULT_MAX_CLL = 10000.0  # Maximum Content Light Level (cd/m²)
DEFAULT_MAX_FALL = 400.0  # Maximum Frame Average Light Level (cd/m²)
DEFAULT_MAX_DISPLAY_MASTERING_LUMINANCE = 1000.0  # Display mastering luminance (cd/m²)
DEFAULT_MIN_DISPLAY_MASTERING_LUMINANCE = 0.0001  # Minimum display luminance (cd/m²)

# Rec.2020 color primaries (ITU-R BT.2020) - Ultra HD/HDR standard
REC2020_RED_PRIMARY = (0.708, 0.292)
REC2020_GREEN_PRIMARY = (0.170, 0.797)
REC2020_BLUE_PRIMARY = (0.131, 0.046)

# D65 white point (CIE 1931) - Standard illuminant
D65_WHITE_POINT = (0.3127, 0.3290)


@dataclass
class DeckLinkSettings:
    """
    Configuration settings for DeckLink device initialization.

    This dataclass holds comprehensive settings for configuring a DeckLink device
    including video resolution, HDR metadata parameters, and color space information.

    Attributes
    ----------
    width : int
        Video output width in pixels. Default is 1920.
    height : int
        Video output height in pixels. Default is 1080.
    no_hdr : bool
        Whether to disable HDR metadata output. Default is False.
    eotf : EOTFType
        Electro-Optical Transfer Function type. Default is PQ (HDR10).
    max_cll : float
        Maximum Content Light Level in cd/m². Default is 10000.0.
    max_fall : float
        Maximum Frame Average Light Level in cd/m². Default is 400.0.
    max_display_mastering_luminance : float
        Maximum display mastering luminance in cd/m². Default is 1000.0.
    min_display_mastering_luminance : float
        Minimum display mastering luminance in cd/m². Default is 0.0001.
    red_primary : tuple[float, float]
        Red primary chromaticity coordinates (x, y). Default is Rec.2020.
    green_primary : tuple[float, float]
        Green primary chromaticity coordinates (x, y). Default is Rec.2020.
    blue_primary : tuple[float, float]
        Blue primary chromaticity coordinates (x, y). Default is Rec.2020.
    white_point : tuple[float, float]
        White point chromaticity coordinates (x, y). Default is D65.
    """

    width: int = DEFAULT_WIDTH
    height: int = DEFAULT_HEIGHT

    # HDR metadata settings
    no_hdr: bool = False
    eotf: EOTFType = EOTFType.PQ
    max_cll: float = DEFAULT_MAX_CLL
    max_fall: float = DEFAULT_MAX_FALL
    max_display_mastering_luminance: float = DEFAULT_MAX_DISPLAY_MASTERING_LUMINANCE
    min_display_mastering_luminance: float = DEFAULT_MIN_DISPLAY_MASTERING_LUMINANCE
    
    # Color space primaries and white point
    red_primary: tuple[float, float] = REC2020_RED_PRIMARY
    green_primary: tuple[float, float] = REC2020_GREEN_PRIMARY
    blue_primary: tuple[float, float] = REC2020_BLUE_PRIMARY
    white_point: tuple[float, float] = D65_WHITE_POINT


@dataclass
class PatternSettings:
    """
    Configuration settings for test pattern generation.

    This dataclass holds settings for generating test patterns including colors,
    bit depth, dimensions, and region of interest parameters.

    Attributes
    ----------
    colors : list[tuple[int, int, int]]
        List of RGB color tuples for pattern generation. Default is red (4095, 0, 0).
    bit_depth : int
        Color bit depth (8, 10, or 12). Default is 12.
    width : int
        Pattern width in pixels. Default is 1920.
    height : int
        Pattern height in pixels. Default is 1080.
    roi_x : int
        Region of interest X offset. Default is 0.
    roi_y : int
        Region of interest Y offset. Default is 0.
    roi_width : int | None
        Region of interest width. None uses full width.
    roi_height : int | None
        Region of interest height. None uses full height.
    """

    colors: list[tuple[int, int, int]] = field(default_factory=lambda: [(4095, 0, 0)])
    bit_depth: int = 12
    width: int = DEFAULT_WIDTH
    height: int = DEFAULT_HEIGHT

    # Region of interest parameters
    roi_x: int = 0
    roi_y: int = 0
    roi_width: int | None = None
    roi_height: int | None = None
