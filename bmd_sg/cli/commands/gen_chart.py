"""
Chart generation CLI command.

Generates display-ready TIFF charts from YAML chart definitions.
"""

from enum import Enum
from pathlib import Path
from typing import Annotated

import numpy as np
import typer
from PIL import Image, ImageDraw, ImageFont
from rich.console import Console

from bmd_sg.charts.color_types import ColorSpace, TransferFunction
from bmd_sg.charts.loaders import load_chart
from bmd_sg.charts.renderer import render_chart
from bmd_sg.charts.tiff_writer import write_chart_tiff

console = Console()


class ColorSpaceOption(str, Enum):
    """CLI color space options."""

    REC709 = "rec709"
    P3 = "p3"
    REC2020 = "rec2020"


class TransferFunctionOption(str, Enum):
    """CLI transfer function options."""

    SRGB = "srgb"
    GAMMA22 = "gamma22"
    LINEAR = "linear"
    PQ = "pq"
    HLG = "hlg"


def gen_chart_command(
    source: Annotated[
        Path,
        typer.Argument(help="Path to YAML chart definition file"),
    ],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output TIFF file path (default: <source>.tif)"),
    ] = None,
    width: Annotated[
        int,
        typer.Option("--width", "-w", help="Output width in pixels"),
    ] = 1920,
    height: Annotated[
        int,
        typer.Option("--height", "-h", help="Output height in pixels"),
    ] = 1080,
    colorspace: Annotated[
        ColorSpaceOption,
        typer.Option("--colorspace", "-c", help="Target color space for output"),
    ] = ColorSpaceOption.REC709,
    transfer: Annotated[
        TransferFunctionOption,
        typer.Option("--transfer", "-t", help="Transfer function"),
    ] = TransferFunctionOption.SRGB,
    bit_depth: Annotated[
        int,
        typer.Option("--bit-depth", "-b", help="Output bit depth (8, 10, 12, 16)"),
    ] = 12,
    labels: Annotated[
        bool,
        typer.Option("--labels/--no-labels", help="Add text labels for measurements"),
    ] = False,
    white_nits: Annotated[
        float,
        typer.Option("--white-nits", help="Reference white luminance in nits"),
    ] = 100.0,
) -> None:
    """
    Generate a display-ready test chart TIFF from a YAML definition.

    Examples:
        bmd-signal-gen gen-chart data/my_chart.yaml -o chart.tif --labels
        bmd-signal-gen gen-chart data/smpte_bars.yaml -o smpte.tif
    """
    # Map CLI options to internal types
    cs_map = {
        ColorSpaceOption.REC709: ColorSpace.REC709,
        ColorSpaceOption.P3: ColorSpace.P3_D65,
        ColorSpaceOption.REC2020: ColorSpace.REC2020,
    }
    tf_map = {
        TransferFunctionOption.SRGB: TransferFunction.SRGB,
        TransferFunctionOption.GAMMA22: TransferFunction.GAMMA_22,
        TransferFunctionOption.LINEAR: TransferFunction.LINEAR,
        TransferFunctionOption.PQ: TransferFunction.PQ,
        TransferFunctionOption.HLG: TransferFunction.HLG,
    }

    target_space = cs_map[colorspace]
    transfer_func = tf_map[transfer]

    # Derive output path from source if not specified
    if output is None:
        output = source.with_suffix(".tif")

    # Load chart
    if not source.exists():
        console.print(f"[red]Error:[/red] File not found: {source}")
        raise typer.Exit(1)

    console.print(f"Loading chart from [cyan]{source}[/cyan]...")
    layout = load_chart(source, include_labels=labels)

    console.print(f"  Chart: {layout.name}")
    console.print(f"  Patches: {len(layout.patches)}")
    console.print(f"  Output: {width}x{height} @ {bit_depth}-bit")
    console.print(f"  Colorspace: {target_space.value}")
    console.print(f"  Transfer: {transfer_func.value}")

    # Render chart
    console.print("Rendering chart...")
    image = render_chart(
        layout=layout,
        width=width,
        height=height,
        bit_depth=bit_depth,
        target_space=target_space,
        transfer_function=transfer_func,
        reference_white_Y=white_nits,
        include_labels=labels,
    )

    # Write TIFF
    console.print(f"Writing TIFF to [cyan]{output}[/cyan]...")
    write_chart_tiff(
        path=output,
        image=image,
        layout=layout,
        colorspace=target_space,
        transfer_function=transfer_func,
        bit_depth=bit_depth,
        reference_white_nits=white_nits,
    )

    # Generate PNG preview with watermark (append _preview before extension)
    preview_path = output.with_stem(output.stem + "_preview").with_suffix(".png")
    console.print(f"Writing preview to [cyan]{preview_path}[/cyan]...")
    _write_preview_png(image, preview_path, bit_depth, width, height)

    console.print("[green]✓[/green] Chart generated successfully!")


def _write_preview_png(
    image: np.ndarray,
    path: Path,
    bit_depth: int,
    width: int,
    height: int,
) -> None:
    """
    Write a PNG preview with "PREVIEW ONLY" watermark.

    Parameters
    ----------
    image : np.ndarray
        Source image data (uint16).
    path : Path
        Output path for PNG.
    bit_depth : int
        Source bit depth for proper scaling.
    width : int
        Image width.
    height : int
        Image height.
    """
    # Convert to 8-bit for PNG
    image_8bit = (image >> (bit_depth - 8)).astype(np.uint8)
    pil_image = Image.fromarray(image_8bit, mode="RGB")

    # Load font for watermark - large size for visibility
    try:
        font_size = max(80, min(width, height) // 8)
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except OSError:
        font = ImageFont.load_default()

    watermark_text = "PREVIEW ONLY"

    # Get text bounding box for centering
    bbox = font.getbbox(watermark_text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Create a transparent overlay for the rotated watermark
    # Make it large enough to hold rotated text
    diagonal = int((text_width**2 + text_height**2) ** 0.5) + 40
    txt_layer = Image.new("RGBA", (diagonal, diagonal), (255, 255, 255, 0))
    txt_draw = ImageDraw.Draw(txt_layer)

    # Draw text centered on the overlay with outline effect
    tx = (diagonal - text_width) // 2
    ty = (diagonal - text_height) // 2

    # Draw black outline (stroke) by drawing text offset in all directions
    outline_color = (0, 0, 0, 200)
    for ox, oy in [(-2, -2), (-2, 2), (2, -2), (2, 2), (-2, 0), (2, 0), (0, -2), (0, 2)]:
        txt_draw.text((tx + ox, ty + oy), watermark_text, font=font, fill=outline_color)

    # Draw red text on top
    txt_draw.text((tx, ty), watermark_text, font=font, fill=(255, 60, 60, 220))

    # Rotate the text layer
    rotated = txt_layer.rotate(15, expand=False, resample=Image.Resampling.BICUBIC)

    # Calculate position to center on main image
    paste_x = (width - rotated.width) // 2
    paste_y = (height - rotated.height) // 2

    # Composite the rotated watermark onto the image
    pil_image.paste(rotated, (paste_x, paste_y), rotated)

    pil_image.save(path, "PNG")
