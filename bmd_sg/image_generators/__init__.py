"""
Deprecated shim for ``display_patterns.image_generators``.

Pattern generation moved to the display-patterns package
(§spec:pattern-library). This module re-exports the display-patterns
equivalents so existing ``bmd_sg.image_generators`` imports keep working
for one release cycle. Import from ``display_patterns.image_generators``
instead.
"""

import warnings

from display_patterns.image_generators import (
    DEFAULT_PATTERN_GENERATOR,
    ROI,
    PatternGenerator,
)

warnings.warn(
    "bmd_sg.image_generators is deprecated; "
    "import display_patterns.image_generators instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "DEFAULT_PATTERN_GENERATOR",
    "ROI",
    "PatternGenerator",
]
