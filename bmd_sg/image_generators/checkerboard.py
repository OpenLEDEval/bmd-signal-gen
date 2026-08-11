"""
Deprecated shim for ``display_patterns.image_generators.checkerboard``.

Pattern generation moved to the display-patterns package
(§spec:pattern-library). This module re-exports the display-patterns
equivalents so existing ``bmd_sg.image_generators.checkerboard`` imports
keep working for one release cycle. Import from
``display_patterns.image_generators.checkerboard`` instead.
"""

from display_patterns.image_generators.checkerboard import (
    DEFAULT_PATTERN_BUFFER,
    DEFAULT_PATTERN_GENERATOR,
    ROI,
    ColorRangeError,
    PatternGenerator,
)

from bmd_sg.utilities import warn_moved

warn_moved(__name__)

__all__ = [
    "DEFAULT_PATTERN_BUFFER",
    "DEFAULT_PATTERN_GENERATOR",
    "ROI",
    "ColorRangeError",
    "PatternGenerator",
]
