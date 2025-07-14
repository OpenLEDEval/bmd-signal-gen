"""
Image generators for BMD signal generation.

This package provides various pattern and image generation utilities for BMD
DeckLink devices, including checkerboard patterns, solid colors, and other
test patterns commonly used in video production and display testing.
"""

from bmd_sg.image_generators.checkerboard import (
    DEFAULT_PATTERN_GENERATOR,
    ROI,
    PatternGenerator,
)

__all__ = [
    "DEFAULT_PATTERN_GENERATOR",
    "ROI",
    "PatternGenerator",
]
