"""
TIFF writer for chart images with embedded JSON metadata.

Writes 16-bit TIFF files with chart metadata in the ImageDescription tag.
"""

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import tifffile
from numpy.typing import NDArray

from bmd_sg.charts.color_types import ChartLayout, ColorSpace, TransferFunction


@dataclass
class ChartMetadata:
    """
    Metadata for a chart TIFF file.

    This is embedded as JSON in the TIFF ImageDescription tag.
    """

    version: str = "1.0"
    chart_name: str = ""
    chart_source: str | None = None
    colorspace: str = "ITU-R BT.709"
    transfer_function: str = "sRGB"
    bit_depth: int = 12
    reference_white_nits: float = 100.0
    created_at: str = ""
    patches: list[dict] | None = None

    def to_json(self) -> str:
        """Convert to JSON string for embedding in TIFF."""
        data = asdict(self)
        return json.dumps({"bmdsg": data}, indent=2)


def write_chart_tiff(
    path: Path | str,
    image: NDArray[np.uint16],
    layout: ChartLayout,
    colorspace: ColorSpace = ColorSpace.REC709,
    transfer_function: TransferFunction = TransferFunction.SRGB,
    bit_depth: int = 12,
    reference_white_nits: float = 100.0,
) -> None:
    """
    Write a chart image to a TIFF file with metadata.

    Parameters
    ----------
    path : Path | str
        Output file path.
    image : NDArray[np.uint16]
        Image data as uint16 array of shape (height, width, 3).
    layout : ChartLayout
        The chart layout (for metadata).
    colorspace : ColorSpace
        The colorspace of the image.
    transfer_function : TransferFunction
        The transfer function used for encoding.
    bit_depth : int
        The bit depth of the image data.
    reference_white_nits : float
        The reference white luminance in nits.
    """
    path = Path(path)

    # Build patch metadata
    patch_info = []
    for patch in layout.patches:
        patch_info.append(
            {
                "name": patch.name,
                "x_pct": patch.x_pct,
                "y_pct": patch.y_pct,
                "width_pct": patch.width_pct,
                "height_pct": patch.height_pct,
                "color_space": patch.color.space.value,
                "color_values": patch.color.values.tolist(),
            }
        )

    # Create metadata
    metadata = ChartMetadata(
        chart_name=layout.name,
        chart_source=layout.source,
        colorspace=colorspace.value,
        transfer_function=transfer_function.value,
        bit_depth=bit_depth,
        reference_white_nits=reference_white_nits,
        created_at=datetime.now(UTC).isoformat(),
        patches=patch_info,
    )

    # Write TIFF with metadata in description
    tifffile.imwrite(
        path,
        image,
        photometric="rgb",
        description=metadata.to_json(),
    )
