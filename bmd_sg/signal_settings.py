from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from bmd_sg.decklink.bmd_decklink import EOTFType
from bmd_sg.pattern_generator import PatternType, DEFAULT_BIT_DEPTH, DEFAULT_COLOR_12BIT
from bmd_sg.signal_generator import (
    DEFAULT_WIDTH, DEFAULT_HEIGHT, DEFAULT_MAX_CLL, DEFAULT_MAX_FALL,
    DEFAULT_MAX_DISPLAY_MASTERING_LUMINANCE, DEFAULT_MIN_DISPLAY_MASTERING_LUMINANCE,
    REC2020_RED_PRIMARY, REC2020_GREEN_PRIMARY, REC2020_BLUE_PRIMARY, D65_WHITE_POINT
)


@dataclass
class SignalSettings:
    """Dataclass to hold all signal generation settings."""

    # Video settings
    width: int = DEFAULT_WIDTH
    height: int = DEFAULT_HEIGHT
    bit_depth: int = DEFAULT_BIT_DEPTH

    # Pattern settings
    pattern: PatternType = PatternType.SOLID
    colors: List[Tuple[int, int, int]] = field(default_factory=lambda: [DEFAULT_COLOR_12BIT])

    # Region of Interest
    roi_x: int = 0
    roi_y: int = 0
    roi_width: Optional[int] = None
    roi_height: Optional[int] = None

    # HDR Metadata
    no_hdr: bool = False
    eotf: EOTFType = EOTFType.PQ
    max_cll: float = 10000.0  # Note: This is different from DEFAULT_MAX_CLL (1000.0) - keeping as is
    max_fall: float = DEFAULT_MAX_FALL
    max_display_mastering_luminance: float = DEFAULT_MAX_DISPLAY_MASTERING_LUMINANCE
    min_display_mastering_luminance: float = DEFAULT_MIN_DISPLAY_MASTERING_LUMINANCE
    red_primary: Tuple[float, float] = REC2020_RED_PRIMARY
    green_primary: Tuple[float, float] = REC2020_GREEN_PRIMARY
    blue_primary: Tuple[float, float] = REC2020_BLUE_PRIMARY
    white_point: Tuple[float, float] = D65_WHITE_POINT
