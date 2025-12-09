"""
Chart generation CLI command.

Generates display-ready TIFF charts from YAML chart definitions.
"""

from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
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
        Path,
        typer.Option("--output", "-o", help="Output TIFF file path"),
    ] = Path("chart.tif"),
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

    console.print("[green]✓[/green] Chart generated successfully!")
