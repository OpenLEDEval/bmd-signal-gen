"""
BMD Signal Generator package.

A cross-platform signal generator for Blackmagic Design DeckLink devices
that outputs test patterns with HDR metadata support.
"""

from bmd_sg.decklink.bmd_decklink import (
    BMDDeckLink,
    DecklinkSettings,
    EOTFType,
    GamutChromaticities,
    HDRMetadata,
    PixelFormatType,
)
from bmd_sg.image_generators.checkerboard import (
    ROI,
    ColorRangeError,
    PatternGenerator,
)

__all__ = [
    "ROI",
    "BMDDeckLink",
    "ColorRangeError",
    "DecklinkSettings",
    "EOTFType",
    "GamutChromaticities",
    "HDRMetadata",
    "PatternGenerator",
    "PixelFormatType",
]
