"""
YAML chart loader.

Loads color chart definitions from YAML files with support for
XYZ and RGB color spaces, patch layouts, and embedded metadata.
"""

from pathlib import Path
from typing import Any

import yaml

from bmd_sg.charts.color_types import (
    AnnotationLayout,
    AnnotationStripe,
    ChartLayout,
    Colorimetry,
    ColorSpace,
    ColorValue,
    Illuminant,
    Patch,
)


def load_chart(
    path: Path | str,
    include_labels: bool = True,
) -> ChartLayout:
    """
    Load a chart from a YAML file.

    Parameters
    ----------
    path : Path | str
        Path to the YAML chart file.
    include_labels : bool
        Whether to generate label text for each patch.

    Returns
    -------
    ChartLayout
        Chart layout with patches.

    Notes
    -----
    YAML format:
    ```yaml
    name: "My Color Chart"
    version: "1.0"

    colorimetry:
      color_space: "XYZ"  # or "Rec.709", "P3-D65", "Rec.2020"
      white_point: [0.3127, 0.329]
      reference_white_Y: 100.0

    patches:
      - name: "White"
        color: [95.04, 99.99, 108.87]
        layout: [0.0, 0.0, 0.5, 0.5]  # left, top, width, height
    ```
    """
    path = Path(path)

    with path.open() as f:
        data = yaml.safe_load(f)

    # Parse metadata
    chart_name = data.get("name", path.stem)
    colorimetry_data = data.get("colorimetry", {})

    # Parse color space
    color_space_str = colorimetry_data.get("color_space", "XYZ")
    color_space_map = {
        "XYZ": ColorSpace.XYZ,
        "Rec.709": ColorSpace.REC709,
        "ITU-R BT.709": ColorSpace.REC709,
        "P3-D65": ColorSpace.P3_D65,
        "Rec.2020": ColorSpace.REC2020,
        "ITU-R BT.2020": ColorSpace.REC2020,
    }
    color_space = color_space_map.get(color_space_str, ColorSpace.XYZ)

    # Parse illuminant (default to D65 for display/broadcast work)
    illuminant_str = colorimetry_data.get("illuminant", "D65")
    try:
        illuminant = Illuminant.parse(illuminant_str)
    except ValueError:
        illuminant = Illuminant.D65  # Safe fallback

    # Parse white point chromaticity
    white_point_list = colorimetry_data.get("white_point", [0.3127, 0.329])
    white_point = (float(white_point_list[0]), float(white_point_list[1]))

    reference_white_Y = colorimetry_data.get("reference_white_Y", 100.0)

    # Create Colorimetry object
    colorimetry = Colorimetry(
        color_space=color_space,
        illuminant=illuminant,
        white_point=white_point,
        reference_white_Y=reference_white_Y,
    )

    # Parse annotations
    annotations_data = data.get("annotations", {})
    annotations = None
    if annotations_data:
        top_stripe = None
        bottom_stripe = None

        if "top_stripe" in annotations_data:
            ts = annotations_data["top_stripe"]
            top_stripe = AnnotationStripe(
                y_start=float(ts.get("y_start", 0.17)),
                y_end=float(ts.get("y_end", 0.21)),
            )

        if "bottom_stripe" in annotations_data:
            bs = annotations_data["bottom_stripe"]
            bottom_stripe = AnnotationStripe(
                y_start=float(bs.get("y_start", 0.79)),
                y_end=float(bs.get("y_end", 0.83)),
            )

        annotations = AnnotationLayout(
            top_stripe=top_stripe,
            bottom_stripe=bottom_stripe,
        )

    # Parse patches
    patches: list[Patch] = []
    patch_list = data.get("patches", [])

    for patch_data in patch_list:
        patch = _parse_patch(
            patch_data,
            color_space=color_space,
            include_labels=include_labels,
            reference_white_Y=reference_white_Y,
        )
        if patch:
            patches.append(patch)

    return ChartLayout(
        name=chart_name,
        patches=patches,
        source=str(path),
        colorimetry=colorimetry,
        annotations=annotations,
    )


def _parse_patch(
    data: dict[str, Any],
    color_space: ColorSpace,
    include_labels: bool,
    reference_white_Y: float,
) -> Patch | None:
    """Parse a single patch from YAML data."""
    name = data.get("name", "")
    if not name:
        return None

    # Parse color
    color_values = data.get("color")
    if color_values is None or len(color_values) != 3:
        return None

    if color_space == ColorSpace.XYZ:
        color = ColorValue.from_xyz(*color_values)
        y_val = color_values[1]
        # Calculate CIE 1931 x,y chromaticity
        x_xyz, y_xyz, z_xyz = color_values
        xyz_sum = x_xyz + y_xyz + z_xyz
        if xyz_sum > 0:
            cie_x = x_xyz / xyz_sum
            cie_y = y_xyz / xyz_sum
        else:
            cie_x = cie_y = 0.0
    else:
        color = ColorValue.from_rgb(*color_values, space=color_space)
        # Approximate luminance for labels
        y_val = (
            0.2126 * color_values[0]
            + 0.7152 * color_values[1]
            + 0.0722 * color_values[2]
        )
        cie_x = cie_y = None  # Not applicable for RGB input

    # Parse layout
    layout = data.get("layout", [0, 0, 1, 1])
    if len(layout) != 4:
        layout = [0, 0, 1, 1]

    left, top, width, height = layout

    # Label text
    label_text = None
    if include_labels:
        # Check if this is a greyscale patch (name starts with "GS")
        is_greyscale = name.strip().upper().startswith("GS")

        if color_space == ColorSpace.XYZ:
            if is_greyscale:
                # Greyscale: just show Y value
                label_text = f"{name}\nY={y_val:.1f}"
            else:
                # Chromatic: show only CIE x,y coordinates
                label_text = f"{name}\nx={cie_x:.4f}\ny={cie_y:.4f}"
        else:
            label_text = f"{name}\nL={y_val:.2f}"

    return Patch(
        name=name,
        x_pct=left,
        y_pct=top,
        width_pct=width,
        height_pct=height,
        color=color,
        label_text=label_text,
    )
