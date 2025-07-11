from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from bmd_sg.decklink.bmd_decklink import EOTFType
from bmd_sg.pattern_generator import PatternType


@dataclass
class DeckLinkSettings:
    """Dataclass to hold all DeckLink device settings."""

    width: int = 1920
    height: int = 1080

    # HDR Metadata
    no_hdr: bool = False
    eotf: EOTFType = EOTFType.PQ
    max_cll: float = 1000.0
    max_fall: float = 400.0
    max_display_mastering_luminance: float = 1000.0
    min_display_mastering_luminance: float = 0.0001
    red_primary: Tuple[float, float] = (0.708, 0.292)
    green_primary: Tuple[float, float] = (0.170, 0.797)
    blue_primary: Tuple[float, float] = (0.131, 0.046)
    white_point: Tuple[float, float] = (0.3127, 0.3290)


@dataclass
class PatternSettings:
    """Dataclass to hold pattern generation settings."""

    pattern: PatternType = PatternType.SOLID
    colors: List[Tuple[int, int, int]] = field(default_factory=lambda: [(4095, 0, 0)])
    bit_depth: int = 12
    width: int = 1920
    height: int = 1080

    # Region of Interest
    roi_x: int = 0
    roi_y: int = 0
    roi_width: Optional[int] = None
    roi_height: Optional[int] = None
