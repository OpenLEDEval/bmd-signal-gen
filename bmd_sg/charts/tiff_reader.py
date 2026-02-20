"""
TIFF reader for loading chart images with embedded metadata.

Loads 16-bit TIFF files written by tiff_writer and returns the raw
numpy array data without any manipulation.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import tifffile
from numpy.typing import NDArray


@dataclass
class TiffMetadata:
    """
    Metadata extracted from a chart TIFF file.

    This is parsed from the JSON in the TIFF ImageDescription tag.
    """

    version: str = "1.0"
    chart_name: str = ""
    chart_source: str | None = None
    colorspace: str = "ITU-R BT.709"
    transfer_function: str = "sRGB"
    bit_depth: int = 12
    reference_white_nits: float = 100.0
    created_at: str = ""
    patches: list[dict[str, Any]] | None = None

    @classmethod
    def from_json(cls, json_str: str) -> "TiffMetadata":
        """Parse metadata from JSON string (from TIFF ImageDescription)."""
        data = json.loads(json_str)

        # Handle both wrapped {"bmdsg": {...}} and unwrapped formats
        if "bmdsg" in data:
            data = data["bmdsg"]

        return cls(
            version=data.get("version", "1.0"),
            chart_name=data.get("chart_name", ""),
            chart_source=data.get("chart_source"),
            colorspace=data.get("colorspace", "ITU-R BT.709"),
            transfer_function=data.get("transfer_function", "sRGB"),
            bit_depth=data.get("bit_depth", 12),
            reference_white_nits=data.get("reference_white_nits", 100.0),
            created_at=data.get("created_at", ""),
            patches=data.get("patches"),
        )


def load_chart_tiff(
    path: Path | str,
) -> tuple[NDArray[np.uint16], TiffMetadata]:
    """
    Load a chart TIFF file and return raw image data with metadata.

    The image data is returned as-is without any scaling or bit manipulation.
    Values are in their native range based on bit_depth from metadata:
    - 8-bit: 0-255
    - 10-bit: 0-1023
    - 12-bit: 0-4095

    Parameters
    ----------
    path : Path | str
        Path to the TIFF file.

    Returns
    -------
    tuple[NDArray[np.uint16], TiffMetadata]
        Tuple of (image_data, metadata).
        image_data has shape (height, width, 3) and dtype uint16.

    Raises
    ------
    FileNotFoundError
        If the TIFF file does not exist.
    ValueError
        If the TIFF file is malformed or missing required metadata.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"TIFF file not found: {path}")

    # Load TIFF file
    with tifffile.TiffFile(path) as tif:
        # Read image data
        image = tif.asarray()

        # Ensure we have RGB data
        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError(
                f"Expected RGB image with shape (H, W, 3), got {image.shape}"
            )

        # Ensure uint16 dtype
        if image.dtype != np.uint16:
            raise ValueError(f"Expected uint16 dtype, got {image.dtype}")

        # Try to extract metadata from ImageDescription
        metadata = TiffMetadata()
        if tif.pages:
            page = tif.pages[0]
            if page.description:
                try:
                    metadata = TiffMetadata.from_json(page.description)
                except (json.JSONDecodeError, KeyError):
                    # Metadata parsing failed, use defaults
                    # This allows loading TIFFs without our custom metadata
                    pass

    return image, metadata
