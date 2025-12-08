"""
Pytest configuration and fixtures for BMD Signal Generator tests.

This module provides common fixtures and configuration for testing
the BMD Signal Generator package, including mock device setup and
common test utilities.
"""

import pytest

from bmd_sg.decklink.bmd_decklink import (
    DecklinkSettings,
    EOTFType,
    GamutChromaticities,
    PixelFormatType,
)
from bmd_sg.image_generators.checkerboard import ROI, PatternGenerator


@pytest.fixture
def default_settings() -> DecklinkSettings:
    """
    Create default DeckLink settings for testing.

    Returns
    -------
    DecklinkSettings
        Settings configured for 1920x1080 with 12-bit RGB and PQ HDR.
    """
    return DecklinkSettings(
        device=0,
        pixel_format=PixelFormatType.FORMAT_12BIT_RGBLE,
        width=1920,
        height=1080,
        roi_x=0,
        roi_y=0,
        roi_width=1920,
        roi_height=1080,
        eotf=EOTFType.PQ,
        max_cll=10000.0,
        max_fall=400.0,
        max_display_mastering_luminance=1000.0,
        min_display_mastering_luminance=0.0,
        gamut_chromaticities=GamutChromaticities(
            red_xy=(0.708, 0.292),
            green_xy=(0.170, 0.797),
            blue_xy=(0.131, 0.046),
            white_xy=(0.3127, 0.3290),
        ),
        no_hdr=False,
    )


@pytest.fixture
def pattern_generator_12bit() -> PatternGenerator:
    """
    Create a 12-bit pattern generator for testing.

    Returns
    -------
    PatternGenerator
        Generator configured for 1920x1080 at 12-bit depth.
    """
    return PatternGenerator(
        bit_depth=12,
        width=1920,
        height=1080,
        roi=ROI(x=0, y=0, width=1920, height=1080),
    )


@pytest.fixture
def pattern_generator_8bit() -> PatternGenerator:
    """
    Create an 8-bit pattern generator for testing.

    Returns
    -------
    PatternGenerator
        Generator configured for 1920x1080 at 8-bit depth.
    """
    return PatternGenerator(
        bit_depth=8,
        width=1920,
        height=1080,
        roi=ROI(x=0, y=0, width=1920, height=1080),
    )


@pytest.fixture
def sample_colors_12bit() -> list[list[int]]:
    """
    Sample 12-bit color values for testing.

    Returns
    -------
    list[list[int]]
        Four colors: white, black, red, green (12-bit range).
    """
    return [
        [4095, 4095, 4095],  # White
        [0, 0, 0],  # Black
        [4095, 0, 0],  # Red
        [0, 4095, 0],  # Green
    ]


@pytest.fixture
def sample_colors_8bit() -> list[list[int]]:
    """
    Sample 8-bit color values for testing.

    Returns
    -------
    list[list[int]]
        Four colors: white, black, red, green (8-bit range).
    """
    return [
        [255, 255, 255],  # White
        [0, 0, 0],  # Black
        [255, 0, 0],  # Red
        [0, 255, 0],  # Green
    ]
