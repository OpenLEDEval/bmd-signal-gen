"""
BMD Signal Generator package.

A cross-platform signal generator for Blackmagic Design DeckLink devices
that outputs test patterns with HDR metadata support.
"""

from display_patterns.image_generators.checkerboard import (
    ROI,
    ColorRangeError,
    PatternGenerator,
)

from bmd_sg.decklink.bmd_decklink import (
    BMDDeckLink,
    DeckLinkOutput,
    DecklinkSettings,
    EOTFType,
    GamutChromaticities,
    HDRMetadata,
    PixelFormatType,
)

__all__ = [
    "ROI",
    "BMDDeckLink",
    "ColorRangeError",
    "DeckLinkOutput",
    "DecklinkSettings",
    "EOTFType",
    "GamutChromaticities",
    "HDRMetadata",
    "PatternGenerator",
    "PixelFormatType",
]
