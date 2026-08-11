"""
Deprecated shim for ``display_patterns.charts.loaders``.

Chart production moved to the display-patterns package
(§spec:pattern-library). This module re-exports the display-patterns
equivalents so existing ``bmd_sg.charts.loaders`` imports keep working
for one release cycle. Import from ``display_patterns.charts.loaders``
instead.
"""

import warnings

from display_patterns.charts.loaders import load_chart

warnings.warn(
    "bmd_sg.charts.loaders is deprecated; "
    "import display_patterns.charts.loaders instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "load_chart",
]
