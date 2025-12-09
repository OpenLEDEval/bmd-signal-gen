"""
Display TIFF command for BMD CLI.

Loads a pre-generated TIFF file and displays it on the DeckLink device.
The TIFF pixel values are passed through exactly as stored, and the
HDMI/SDI signaling metadata is configured based on the embedded TIFF metadata.
"""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from bmd_sg.charts.tiff_reader import load_chart_tiff
from bmd_sg.cli.shared import (
    display_image_for_duration,
    get_device_settings,
    initialize_device,
    is_mock_mode_enabled,
)
from bmd_sg.decklink.bmd_decklink import (
    colorspace_to_gamut_chromaticities,
    transfer_function_to_eotf,
)

console = Console()


def display_tiff_command(
    ctx: typer.Context,
    tiff_path: Annotated[
        Path,
        typer.Argument(help="Path to the TIFF file to display"),
    ],
    duration: Annotated[
        float,
        typer.Option(
            "--duration",
            "-t",
            help="Duration in seconds to display the image (0 = indefinitely)",
        ),
    ] = 5.0,
) -> None:
    """
    Display a pre-generated TIFF file on the DeckLink device.

    The TIFF pixel values are passed through exactly as stored, without
    any scaling or color conversion. The HDMI/SDI signaling metadata
    (EOTF, color primaries) is configured based on the embedded TIFF metadata.

    Examples:
        bmd-signal-gen display-tiff chart.tif --duration 10
        bmd-signal-gen --device 1 display-tiff pattern.tif
    """
    # Check file exists
    if not tiff_path.exists():
        console.print(f"[red]Error:[/red] File not found: {tiff_path}")
        raise typer.Exit(1)

    # Load TIFF
    console.print(f"Loading TIFF from [cyan]{tiff_path}[/cyan]...")
    try:
        image, metadata = load_chart_tiff(tiff_path)
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e

    # Display metadata info
    console.print(f"  Chart: {metadata.chart_name or '(unnamed)'}")
    console.print(f"  Dimensions: {image.shape[1]}x{image.shape[0]}")
    console.print(f"  Bit depth: {metadata.bit_depth}-bit")
    console.print(f"  Colorspace: {metadata.colorspace}")
    console.print(f"  Transfer: {metadata.transfer_function}")

    # Get device settings and override with TIFF metadata
    settings = get_device_settings(ctx)
    use_mock = is_mock_mode_enabled(ctx)

    # Map TIFF metadata to DeckLink settings
    # This ensures HDMI/SDI signaling matches the TIFF content
    settings.gamut_chromaticities = colorspace_to_gamut_chromaticities(
        metadata.colorspace
    )
    settings.eotf = transfer_function_to_eotf(metadata.transfer_function)

    console.print(
        f"\n[bold]Configuring HDMI/SDI signaling from TIFF metadata:[/bold]"
    )
    console.print(f"  EOTF: {settings.eotf}")
    console.print(f"  Primaries: {metadata.colorspace}")

    console.print("\nInitializing DeckLink device...")
    decklink = initialize_device(settings, use_mock=use_mock)

    # Display the image
    console.print(
        f"[green]✓[/green] Displaying TIFF "
        f"({image.shape[1]}x{image.shape[0]} @ {metadata.bit_depth}-bit)..."
    )
    display_image_for_duration(decklink, image, duration)

    console.print("[green]✓[/green] Done.")


__all__ = ["display_tiff_command"]
