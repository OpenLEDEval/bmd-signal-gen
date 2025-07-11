from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from bmd_sg.decklink.bmd_decklink import EOTFType
from bmd_sg.pattern_generator import PatternType, DEFAULT_BIT_DEPTH, DEFAULT_COLOR_12BIT

# Video resolution constants
DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080

# HDR metadata constants
DEFAULT_MAX_CLL = 1000.0
DEFAULT_MAX_FALL = 400.0
DEFAULT_MAX_DISPLAY_MASTERING_LUMINANCE = 1000.0
DEFAULT_MIN_DISPLAY_MASTERING_LUMINANCE = 0.0001

# Rec.2020 color primaries (ITU-R BT.2020)
REC2020_RED_PRIMARY = (0.708, 0.292)
REC2020_GREEN_PRIMARY = (0.170, 0.797)
REC2020_BLUE_PRIMARY = (0.131, 0.046)

# D65 white point (CIE 1931)
D65_WHITE_POINT = (0.3127, 0.3290)


@dataclass
class DeckLinkSettings:
    """Dataclass to hold all DeckLink device settings."""

    width: int = DEFAULT_WIDTH
    height: int = DEFAULT_HEIGHT

    # HDR Metadata
    no_hdr: bool = False
    eotf: EOTFType = EOTFType.PQ
    max_cll: float = DEFAULT_MAX_CLL
    max_fall: float = DEFAULT_MAX_FALL
    max_display_mastering_luminance: float = DEFAULT_MAX_DISPLAY_MASTERING_LUMINANCE
    min_display_mastering_luminance: float = DEFAULT_MIN_DISPLAY_MASTERING_LUMINANCE
    red_primary: Tuple[float, float] = REC2020_RED_PRIMARY
    green_primary: Tuple[float, float] = REC2020_GREEN_PRIMARY
    blue_primary: Tuple[float, float] = REC2020_BLUE_PRIMARY
    white_point: Tuple[float, float] = D65_WHITE_POINT


@dataclass
class PatternSettings:
    """Dataclass to hold pattern generation settings."""

    pattern: PatternType = PatternType.SOLID
    colors: List[Tuple[int, int, int]] = field(default_factory=lambda: [DEFAULT_COLOR_12BIT])
    bit_depth: int = DEFAULT_BIT_DEPTH
    width: int = DEFAULT_WIDTH
    height: int = DEFAULT_HEIGHT

    # Region of Interest
    roi_x: int = 0
    roi_y: int = 0
    roi_width: Optional[int] = None
    roi_height: Optional[int] = None
