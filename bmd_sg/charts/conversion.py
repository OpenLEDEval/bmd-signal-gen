"""
Color space conversion utilities using colour-science.

This module wraps the colour-science library for XYZ to RGB conversion
with proper illuminant handling and transfer function encoding.
"""

import colour
import numpy as np
from numpy.typing import NDArray

from bmd_sg.charts.color_types import ColorSpace, ColorValue, Illuminant, TransferFunction


def xyz_to_display_rgb(
    color: ColorValue,
    target_space: ColorSpace = ColorSpace.REC709,
    transfer_function: TransferFunction = TransferFunction.SRGB,
    reference_white_Y: float = 100.0,
    illuminant: Illuminant = Illuminant.D65,
) -> NDArray[np.float64]:
    """
    Convert XYZ color value to display-ready RGB.

    Parameters
    ----------
    color : ColorValue
        Input color in XYZ space.
    target_space : ColorSpace
        Target RGB color space.
    transfer_function : TransferFunction
        Transfer function to apply (encoding).
    reference_white_Y : float
        The Y value that corresponds to white (default 100 for Y=100 normalized data).
    illuminant : Illuminant
        The CIE standard illuminant the XYZ values are referenced to.
        This must match the illuminant used when the XYZ values were calculated.

    Returns
    -------
    NDArray[np.float64]
        Encoded RGB values in range [0, 1].

    Raises
    ------
    ValueError
        If input color is not in XYZ space.
    """
    if color.space != ColorSpace.XYZ:
        msg = f"Expected XYZ color, got {color.space}"
        raise ValueError(msg)

    # Normalize XYZ by reference white Y
    xyz_normalized = color.values / reference_white_Y

    # Map our ColorSpace enum to colour-science colorspace names
    colorspace_map = {
        ColorSpace.REC709: "ITU-R BT.709",
        ColorSpace.P3_D65: "P3-D65",
        ColorSpace.REC2020: "ITU-R BT.2020",
    }
    cs_name = colorspace_map.get(target_space)
    if cs_name is None:
        msg = f"Unsupported target colorspace: {target_space}"
        raise ValueError(msg)

    # Get the colorspace definition
    cs = colour.RGB_COLOURSPACES[cs_name]

    # Map our Illuminant enum to colour-science illuminant names
    illuminant_xy = colour.CCS_ILLUMINANTS["CIE 1931 2 Degree Standard Observer"][
        illuminant.value
    ]

    # XYZ to linear RGB using colour-science
    # Uses the illuminant from chart metadata
    linear_rgb = colour.XYZ_to_RGB(
        xyz_normalized,
        colourspace=cs,
        illuminant=illuminant_xy,
    )

    # Clip to gamut
    linear_rgb = np.clip(linear_rgb, 0.0, 1.0)

    # Apply transfer function (encoding)
    if transfer_function == TransferFunction.LINEAR:
        encoded_rgb = linear_rgb
    elif transfer_function == TransferFunction.SRGB:
        encoded_rgb = colour.cctf_encoding(linear_rgb, function="sRGB")
    elif transfer_function == TransferFunction.GAMMA_22:
        encoded_rgb = np.power(linear_rgb, 1.0 / 2.2)
    elif transfer_function == TransferFunction.PQ:
        # PQ expects absolute luminance in cd/m², need to scale
        # For now, assume reference_white maps to SDR white level
        encoded_rgb = colour.cctf_encoding(
            linear_rgb, function="ST 2084", L_p=10000  # noqa: N803
        )
    elif transfer_function == TransferFunction.HLG:
        encoded_rgb = colour.cctf_encoding(linear_rgb, function="HLG")
    else:
        msg = f"Unsupported transfer function: {transfer_function}"
        raise ValueError(msg)

    return np.asarray(encoded_rgb, dtype=np.float64)


def rgb_to_xyz(
    color: ColorValue,
    reference_white_Y: float = 100.0,
    illuminant: Illuminant = Illuminant.D65,
) -> ColorValue:
    """
    Convert RGB color value to XYZ.

    Parameters
    ----------
    color : ColorValue
        Input color in an RGB space.
    reference_white_Y : float
        The Y value for white (for denormalization).
    illuminant : Illuminant
        The CIE standard illuminant for the output XYZ values.

    Returns
    -------
    ColorValue
        Color in XYZ space.
    """
    if color.space == ColorSpace.XYZ:
        return color

    colorspace_map = {
        ColorSpace.REC709: "ITU-R BT.709",
        ColorSpace.P3_D65: "P3-D65",
        ColorSpace.REC2020: "ITU-R BT.2020",
    }
    cs_name = colorspace_map.get(color.space)
    if cs_name is None:
        msg = f"Unsupported source colorspace: {color.space}"
        raise ValueError(msg)

    cs = colour.RGB_COLOURSPACES[cs_name]

    # Map our Illuminant enum to colour-science illuminant names
    illuminant_xy = colour.CCS_ILLUMINANTS["CIE 1931 2 Degree Standard Observer"][
        illuminant.value
    ]

    xyz_normalized = colour.RGB_to_XYZ(
        color.values,
        colourspace=cs,
        illuminant=illuminant_xy,
    )

    xyz = xyz_normalized * reference_white_Y

    return ColorValue(values=np.asarray(xyz, dtype=np.float64), space=ColorSpace.XYZ)
