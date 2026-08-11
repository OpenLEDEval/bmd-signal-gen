"""
Tests for the deprecation shims left behind by the display-patterns split.

Pattern and chart unit tests live upstream in display-patterns. Here we
assert only the compatibility contract (§spec:pattern-library): every
legacy ``bmd_sg`` import path still works, emits a DeprecationWarning,
and re-exports the display-patterns objects unchanged.
"""

import importlib
import sys

import pytest

SHIM_MODULES = [
    "bmd_sg.image_generators",
    "bmd_sg.image_generators.checkerboard",
    "bmd_sg.charts",
    "bmd_sg.charts.color_types",
    "bmd_sg.charts.conversion",
    "bmd_sg.charts.renderer",
    "bmd_sg.charts.tiff_reader",
    "bmd_sg.charts.tiff_writer",
    "bmd_sg.charts.loaders",
    "bmd_sg.charts.loaders.yaml_chart",
]


@pytest.mark.parametrize("module_name", SHIM_MODULES)
def test_shim_imports_warns_and_reexports(module_name: str) -> None:
    """
    Import a legacy module path and check the shim contract.

    Parameters
    ----------
    module_name : str
        Legacy ``bmd_sg`` module path to import.
    """
    sys.modules.pop(module_name, None)
    with pytest.warns(DeprecationWarning, match=module_name):
        module = importlib.import_module(module_name)

    upstream_name = module_name.replace("bmd_sg.", "display_patterns.", 1)
    upstream = importlib.import_module(upstream_name)
    assert module.__all__
    for name in module.__all__:
        assert getattr(module, name) is getattr(upstream, name)
