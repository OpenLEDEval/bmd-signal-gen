"""
Deprecated shim for ``display_patterns.charts.color_types``.

Chart production moved to the display-patterns package
(§spec:pattern-library). This module re-exports the display-patterns
equivalents so existing ``bmd_sg.charts.color_types`` imports keep
working for one release cycle. Import from
``display_patterns.charts.color_types`` instead.
"""

import warnings

from display_patterns.charts.color_types import (
    AnnotationLayout,
    AnnotationStripe,
    Canvas,
    ChartLayout,
    Colorimetry,
    ColorSpace,
    ColorValue,
    Illuminant,
    LightSource,
    Patch,
    PatternType,
    TransferFunction,
)

warnings.warn(
    "bmd_sg.charts.color_types is deprecated; "
    "import display_patterns.charts.color_types instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "AnnotationLayout",
    "AnnotationStripe",
    "Canvas",
    "ChartLayout",
    "ColorSpace",
    "ColorValue",
    "Colorimetry",
    "Illuminant",
    "LightSource",
    "Patch",
    "PatternType",
    "TransferFunction",
]
