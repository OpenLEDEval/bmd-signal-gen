"""
Deprecated shim for ``display_patterns.charts.loaders.yaml_chart``.

Chart production moved to the display-patterns package
(§spec:pattern-library). This module re-exports the display-patterns
equivalents so existing ``bmd_sg.charts.loaders.yaml_chart`` imports
keep working for one release cycle. Import from
``display_patterns.charts.loaders.yaml_chart`` instead.
"""

from display_patterns.charts.loaders.yaml_chart import load_chart

from bmd_sg.utilities import warn_moved

warn_moved(__name__)

__all__ = [
    "load_chart",
]
