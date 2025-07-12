"""
Comprehensive signal generation settings.

This module provides unified settings for signal generation combining device
configuration, pattern generation, and HDR metadata into a single interface.
"""

from dataclasses import dataclass, field

from bmd_sg.decklink.bmd_decklink import EOTFType
from bmd_sg.signal_generator import (
    D65_WHITE_POINT,
    DEFAULT_HEIGHT,
    DEFAULT_MAX_CLL,
    DEFAULT_MAX_DISPLAY_MASTERING_LUMINANCE,
    DEFAULT_MAX_FALL,
    DEFAULT_MIN_DISPLAY_MASTERING_LUMINANCE,
    DEFAULT_WIDTH,
    REC2020_BLUE_PRIMARY,
    REC2020_GREEN_PRIMARY,
    REC2020_RED_PRIMARY,
)

# Pattern generation constants
DEFAULT_BIT_DEPTH = 12
DEFAULT_COLOR_12BIT = (4095, 0, 0)  # Red color in 12-bit


@dataclass
class SignalSettings:
    """
    Comprehensive signal generation settings combining all configuration options.

    This dataclass provides a unified interface for configuring signal generation
    including video resolution, pattern generation, region of interest, and HDR
    metadata parameters. It combines settings from both device configuration and
    pattern generation into a single convenient interface.

    Attributes
    ----------
    width : int
        Video output width in pixels. Default is 1920.
    height : int
        Video output height in pixels. Default is 1080.
    bit_depth : int
        Color bit depth (8, 10, or 12). Default is 12.
    colors : list[tuple[int, int, int]]
        List of RGB color tuples for pattern generation. Default is red (4095, 0, 0).
    roi_x : int
        Region of interest X offset. Default is 0.
    roi_y : int
        Region of interest Y offset. Default is 0.
    roi_width : int | None
        Region of interest width. None uses full width.
    roi_height : int | None
        Region of interest height. None uses full height.
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

    # Video output settings
    width: int = DEFAULT_WIDTH
    height: int = DEFAULT_HEIGHT
    bit_depth: int = DEFAULT_BIT_DEPTH

    # Pattern generation settings
    colors: list[tuple[int, int, int]] = field(
        default_factory=lambda: [DEFAULT_COLOR_12BIT]
    )

    # Region of interest parameters
    roi_x: int = 0
    roi_y: int = 0
    roi_width: int | None = None
    roi_height: int | None = None

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
