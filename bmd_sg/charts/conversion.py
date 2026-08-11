"""
Deprecated shim for ``display_patterns.charts.conversion``.

Chart production moved to the display-patterns package
(§spec:pattern-library). This module re-exports the display-patterns
equivalents so existing ``bmd_sg.charts.conversion`` imports keep
working for one release cycle. Import from
``display_patterns.charts.conversion`` instead.
"""

import warnings

from display_patterns.charts.conversion import (
    apply_chromatic_adaptation,
    rgb_to_xyz,
    xyz_to_display_rgb,
)

warnings.warn(
    "bmd_sg.charts.conversion is deprecated; "
    "import display_patterns.charts.conversion instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "apply_chromatic_adaptation",
    "rgb_to_xyz",
    "xyz_to_display_rgb",
]
