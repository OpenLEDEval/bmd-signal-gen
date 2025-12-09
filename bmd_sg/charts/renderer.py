"""
Chart renderer for generating images from chart layouts.

Renders charts to numpy arrays with optional text labels for
measurement validation.
"""

import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageDraw, ImageFont

from bmd_sg.charts.color_types import (
    AnnotationLayout,
    ChartLayout,
    ColorSpace,
    Illuminant,
    TransferFunction,
)
from bmd_sg.charts.conversion import xyz_to_display_rgb


def render_chart(
    layout: ChartLayout,
    width: int = 1920,
    height: int = 1080,
    bit_depth: int = 12,
    target_space: ColorSpace = ColorSpace.REC709,
    transfer_function: TransferFunction = TransferFunction.SRGB,
    reference_white_Y: float = 100.0,
    include_labels: bool = False,
) -> NDArray[np.uint16]:
    """
    Render a chart layout to a numpy array.

    Parameters
    ----------
    layout : ChartLayout
        The chart layout to render.
    width : int
        Output width in pixels.
    height : int
        Output height in pixels.
    bit_depth : int
        Output bit depth (8, 10, 12, or 16).
    target_space : ColorSpace
        Target RGB color space for conversion.
    transfer_function : TransferFunction
        Transfer function for encoding.
    reference_white_Y : float
        Reference white Y value for XYZ normalization.
    include_labels : bool
        Whether to render text labels on patches.

    Returns
    -------
    NDArray[np.uint16]
        Image data as uint16 array of shape (height, width, 3).
    """
    max_value = 2**bit_depth - 1

    # Create image as float first
    image = np.zeros((height, width, 3), dtype=np.float64)

    # Get illuminant from chart colorimetry (default to D65)
    illuminant = Illuminant.D65
    if layout.colorimetry is not None:
        illuminant = layout.colorimetry.illuminant

    for patch in layout.patches:
        # Calculate pixel bounds
        x0 = int(patch.x_pct * width)
        y0 = int(patch.y_pct * height)
        x1 = int((patch.x_pct + patch.width_pct) * width)
        y1 = int((patch.y_pct + patch.height_pct) * height)

        # Convert color to target space
        if patch.color.space == ColorSpace.XYZ:
            rgb = xyz_to_display_rgb(
                patch.color,
                target_space=target_space,
                transfer_function=transfer_function,
                reference_white_Y=reference_white_Y,
                illuminant=illuminant,
            )
        elif patch.color.space == target_space:
            # Already in target space, just apply transfer function
            if transfer_function == TransferFunction.LINEAR:
                rgb = patch.color.values
            elif transfer_function == TransferFunction.SRGB:
                import colour

                rgb = colour.cctf_encoding(patch.color.values, function="sRGB")
            elif transfer_function == TransferFunction.GAMMA_22:
                rgb = np.power(patch.color.values, 1.0 / 2.2)
            else:
                rgb = patch.color.values
        else:
            # Need cross-colorspace conversion - for now just use values directly
            rgb = patch.color.values

        # Fill patch area
        image[y0:y1, x0:x1, :] = rgb

    # Convert to uint16
    image_uint16 = np.clip(image * max_value, 0, max_value).astype(np.uint16)

    # Add text labels on patches if requested
    if include_labels:
        image_uint16 = _add_labels(image_uint16, layout, width, height, bit_depth)

    # Always add annotation stripes (critical encoding/chart metadata)
    image_uint16 = _add_annotation_stripes(
        image_uint16,
        layout=layout,
        width=width,
        height=height,
        bit_depth=bit_depth,
        target_space=target_space,
        transfer_function=transfer_function,
        reference_white_Y=reference_white_Y,
    )

    return image_uint16


def _add_labels(
    image: NDArray[np.uint16],
    layout: ChartLayout,
    width: int,
    height: int,
    bit_depth: int,
) -> NDArray[np.uint16]:
    """
    Add text labels to the rendered image using Pillow.

    Parameters
    ----------
    image : NDArray[np.uint16]
        The image to add labels to.
    layout : ChartLayout
        The chart layout with patch information.
    width : int
        Image width.
    height : int
        Image height.
    bit_depth : int
        Bit depth for scaling.

    Returns
    -------
    NDArray[np.uint16]
        Image with labels added.
    """
    # Convert to 8-bit for Pillow (scale down)
    image_8bit = (image >> (bit_depth - 8)).astype(np.uint8)

    # Create Pillow image
    pil_image = Image.fromarray(image_8bit, mode="RGB")
    draw = ImageDraw.Draw(pil_image)

    # Try to load a font, fall back to default
    try:
        font_size = max(12, min(width, height) // 50)
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except OSError:
        font = ImageFont.load_default()

    for patch in layout.patches:
        if not patch.label_text:
            continue

        # Calculate patch center
        x_center = int((patch.x_pct + patch.width_pct / 2) * width)
        y_center = int((patch.y_pct + patch.height_pct / 2) * height)

        # Determine text color based on patch luminance
        # Use contrasting color (white for dark patches, black for light)
        if patch.color.space == ColorSpace.XYZ:
            luminance = patch.color.values[1] / 100.0  # Y component
        else:
            # Approximate luminance from RGB
            luminance = 0.2126 * patch.color.values[0] + 0.7152 * patch.color.values[1]
            luminance += 0.0722 * patch.color.values[2]

        text_color = (0, 0, 0) if luminance > 0.5 else (255, 255, 255)

        # Draw text centered on patch
        draw.text(
            (x_center, y_center),
            patch.label_text,
            fill=text_color,
            font=font,
            anchor="mm",
        )

    # Convert back to bit depth
    result_8bit = np.array(pil_image)
    result = (result_8bit.astype(np.uint16) << (bit_depth - 8)).astype(np.uint16)

    return result


def _add_annotation_stripes(
    image: NDArray[np.uint16],
    layout: ChartLayout,
    width: int,
    height: int,
    bit_depth: int,
    target_space: ColorSpace,
    transfer_function: TransferFunction,
    reference_white_Y: float,
) -> NDArray[np.uint16]:
    """
    Add annotation stripes in the gap regions between chroma and greyscale patches.

    The top stripe (y: 0.17-0.21) shows encoding information.
    The bottom stripe (y: 0.79-0.83) shows chart metadata.

    Parameters
    ----------
    image : NDArray[np.uint16]
        The image to add annotations to.
    layout : ChartLayout
        The chart layout with metadata.
    width : int
        Image width.
    height : int
        Image height.
    bit_depth : int
        Bit depth for scaling.
    target_space : ColorSpace
        Target color space used for encoding.
    transfer_function : TransferFunction
        Transfer function used for encoding.
    reference_white_Y : float
        Reference white Y value used.

    Returns
    -------
    NDArray[np.uint16]
        Image with annotation stripes added.
    """
    # Convert to 8-bit for Pillow
    image_8bit = (image >> (bit_depth - 8)).astype(np.uint8)

    # Create Pillow image
    pil_image = Image.fromarray(image_8bit, mode="RGB")
    draw = ImageDraw.Draw(pil_image)

    # Load font - slightly smaller for annotation text
    try:
        font_size = max(14, min(width, height) // 60)
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except OSError:
        font = ImageFont.load_default()

    # Get stripe positions from layout annotations (or use defaults)
    if layout.annotations and layout.annotations.top_stripe:
        top_stripe_y = int(layout.annotations.top_stripe.y_start * height)
        top_stripe_end = int(layout.annotations.top_stripe.y_end * height)
    else:
        top_stripe_y = int(0.17 * height)
        top_stripe_end = int(0.21 * height)

    if layout.annotations and layout.annotations.bottom_stripe:
        bottom_stripe_y = int(layout.annotations.bottom_stripe.y_start * height)
        bottom_stripe_end = int(layout.annotations.bottom_stripe.y_end * height)
    else:
        bottom_stripe_y = int(0.79 * height)
        bottom_stripe_end = int(0.83 * height)

    # Calculate stripe center Y positions
    top_center_y = (top_stripe_y + top_stripe_end) // 2
    bottom_center_y = (bottom_stripe_y + bottom_stripe_end) // 2

    # Text color (white on black background)
    text_color = (255, 255, 255)

    # Build annotation strings
    # Top stripe: Encoding information
    colorspace_name = target_space.value
    transfer_name = transfer_function.value
    max_code = 2**bit_depth - 1
    # Currently always full range (0 to max_value)
    range_type = "Full"

    top_text = (
        f"{colorspace_name}  │  "
        f"{transfer_name}  │  "
        f"{bit_depth}-bit {range_type} (0-{max_code})"
    )

    # Bottom stripe: Chart metadata
    chart_name = layout.name if layout.name else "Unnamed Chart"
    illuminant_name = layout.colorimetry.illuminant.value if layout.colorimetry else "D65"
    white_info = f"Illuminant: {illuminant_name}  │  Ref White Y: {reference_white_Y}"

    bottom_text = f"{chart_name}  │  {white_info}"

    # Draw top annotation stripe text (centered horizontally)
    draw.text(
        (width // 2, top_center_y),
        top_text,
        fill=text_color,
        font=font,
        anchor="mm",
    )

    # Draw bottom annotation stripe text (centered horizontally)
    draw.text(
        (width // 2, bottom_center_y),
        bottom_text,
        fill=text_color,
        font=font,
        anchor="mm",
    )

    # Convert back to bit depth
    result_8bit = np.array(pil_image)
    result = (result_8bit.astype(np.uint16) << (bit_depth - 8)).astype(np.uint16)

    return result

