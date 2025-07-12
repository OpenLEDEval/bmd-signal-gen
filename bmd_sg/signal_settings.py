from dataclasses import dataclass, field

from bmd_sg.decklink.bmd_decklink import EOTFType
from bmd_sg.pattern_generator import DEFAULT_BIT_DEPTH, DEFAULT_COLOR_12BIT, PatternType
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


@dataclass
class SignalSettings:
    """Dataclass to hold all signal generation settings."""

    # Video settings
    width: int = DEFAULT_WIDTH
    height: int = DEFAULT_HEIGHT
    bit_depth: int = DEFAULT_BIT_DEPTH

    # Pattern settings
    pattern: PatternType = PatternType.SOLID
    colors: list[tuple[int, int, int]] = field(
        default_factory=lambda: [DEFAULT_COLOR_12BIT]
    )

    # Region of Interest
    roi_x: int = 0
    roi_y: int = 0
    roi_width: int | None = None
    roi_height: int | None = None

    # HDR Metadata
    no_hdr: bool = False
    eotf: EOTFType = EOTFType.PQ
    max_cll: float = DEFAULT_MAX_CLL
    max_fall: float = DEFAULT_MAX_FALL
    max_display_mastering_luminance: float = DEFAULT_MAX_DISPLAY_MASTERING_LUMINANCE
    min_display_mastering_luminance: float = DEFAULT_MIN_DISPLAY_MASTERING_LUMINANCE
    red_primary: tuple[float, float] = REC2020_RED_PRIMARY
    green_primary: tuple[float, float] = REC2020_GREEN_PRIMARY
    blue_primary: tuple[float, float] = REC2020_BLUE_PRIMARY
    white_point: tuple[float, float] = D65_WHITE_POINT
