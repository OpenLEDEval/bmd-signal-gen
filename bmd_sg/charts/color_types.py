"""
Deprecated shim for ``display_patterns.charts.color_types``.

Chart production moved to the display-patterns package
(§spec:pattern-library). This module re-exports the display-patterns
equivalents so existing ``bmd_sg.charts.color_types`` imports keep
working for one release cycle. Import from
``display_patterns.charts.color_types`` instead.
"""

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

from bmd_sg.utilities import warn_moved

warn_moved(__name__)

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
