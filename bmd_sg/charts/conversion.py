"""
Color space conversion utilities using colour-science.

This module wraps the colour-science library for XYZ to RGB conversion
with proper illuminant handling and transfer function encoding.
"""

import colour
import numpy as np
from numpy.typing import NDArray

from bmd_sg.charts.color_types import ColorSpace, ColorValue, Illuminant, LightSource, TransferFunction


def apply_chromatic_adaptation(
    xyz: NDArray[np.float64],
    source_illuminant: Illuminant,
    target_light_source: LightSource,
    transform: str = "Bradford",
) -> NDArray[np.float64]:
    """
    Apply chromatic adaptation to simulate different illumination.

    This transforms XYZ values from one illuminant to another, simulating
    how a surface would appear when lit by a different light source.

    Parameters
    ----------
    xyz : NDArray[np.float64]
        XYZ tristimulus values (normalized, Y=1 for white).
    source_illuminant : Illuminant
        The CIE standard illuminant the XYZ values were measured/calculated under.
    target_light_source : LightSource
        The light source to simulate (CCT or D-series illuminant).
    transform : str
        Chromatic adaptation transform to use. Default is "Bradford".
        Other options: "Von Kries", "CAT02", "CAT16".

    Returns
    -------
    NDArray[np.float64]
        Adapted XYZ values under the target illuminant.

    Notes
    -----
    The Bradford transform is the industry standard for most applications.
    It handles blue adaptation better than Von Kries.

    Examples
    --------
    >>> # Simulate D65 chart lit by 5600K light
    >>> xyz_d65 = np.array([0.95, 1.0, 1.09])
    >>> light_5600k = LightSource(cct=5600)
    >>> xyz_adapted = apply_chromatic_adaptation(
    ...     xyz_d65, Illuminant.D65, light_5600k
    ... )
    """
    # Get source white point from illuminant
    source_xy = colour.CCS_ILLUMINANTS["CIE 1931 2 Degree Standard Observer"][
        source_illuminant.value
    ]
    source_XYZ = colour.xy_to_XYZ(source_xy)

    # Get target white point from light source
    target_xy = target_light_source.to_xy()
    target_XYZ = colour.xy_to_XYZ(target_xy)

    # Apply chromatic adaptation transform
    adapted_xyz = colour.chromatic_adaptation(
        XYZ=xyz,
        XYZ_w=source_XYZ,
        XYZ_wr=target_XYZ,
        transform=transform,
    )

    return np.asarray(adapted_xyz, dtype=np.float64)


def xyz_to_display_rgb(
    color: ColorValue,
    target_space: ColorSpace = ColorSpace.REC709,
    transfer_function: TransferFunction = TransferFunction.SRGB,
    reference_white_Y: float = 100.0,
    illuminant: Illuminant = Illuminant.D65,
    simulation_light_source: LightSource | None = None,
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
    simulation_light_source : LightSource | None
        If provided, apply chromatic adaptation to simulate how the chart would
        appear when lit by this light source (CCT or D-series illuminant).
        The adaptation is applied before XYZ→RGB conversion.

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

    # Apply chromatic adaptation if simulating different illumination
    if simulation_light_source is not None:
        xyz_normalized = apply_chromatic_adaptation(
            xyz_normalized,
            source_illuminant=illuminant,
            target_light_source=simulation_light_source,
        )

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

    # Get the illuminant for XYZ→RGB conversion
    # IMPORTANT: After chromatic adaptation, we want the color shift to remain
    # visible on the display. We use the colorspace's native white point (D65)
    # so that the adapted XYZ values are NOT reverse-adapted back.
    #
    # If no simulation is applied, we use the chart's native illuminant so that
    # colours are correctly adapted to the display's D65 white point.
    if simulation_light_source is not None:
        # After CAT: use colorspace native white point to preserve the color shift
        # The adapted XYZ already contains the "warmth" we want to show
        illuminant_xy = cs.whitepoint
    else:
        # No simulation: use chart illuminant for proper display adaptation
        illuminant_xy = colour.CCS_ILLUMINANTS["CIE 1931 2 Degree Standard Observer"][
            illuminant.value
        ]

    # XYZ to linear RGB using colour-science
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
