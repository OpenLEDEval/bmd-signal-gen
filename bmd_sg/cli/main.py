#!/usr/bin/env python3
"""
BMD CLI - Main application with global device configuration.

This module provides the main CLI application with a top-level callback
for global device and HDR parameters, and pattern-specific subcommands.
"""

from typing import Annotated

import typer

from bmd_sg.decklink.bmd_decklink import DecklinkSettings, EOTFType, PixelFormatType

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="BMD Pattern Generator - Output test patterns to Blackmagic Design DeckLink devices",
)


@app.callback()
def main(
    ctx: typer.Context,
    # Device / Pixel Format
    device: Annotated[
        int,
        typer.Option(
            "--device",
            "-d",
            help="Device index",
            rich_help_panel="Device / Pixel Format",
        ),
    ] = 0,
    pixel_format: Annotated[
        PixelFormatType | None,
        typer.Option(
            "--pixel-format",
            "-p",
            help="Pixel format (auto-select if not specified)",
            rich_help_panel="Device / Pixel Format",
        ),
    ] = None,
    width: Annotated[
        int,
        typer.Option(
            "--width", help="Image width", rich_help_panel="Device / Pixel Format"
        ),
    ] = 1920,
    height: Annotated[
        int,
        typer.Option(
            "--height", help="Image height", rich_help_panel="Device / Pixel Format"
        ),
    ] = 1080,
    # ROI
    roi_x: Annotated[
        int, typer.Option("--roi-x", help="ROI X offset", rich_help_panel="ROI")
    ] = 0,
    roi_y: Annotated[
        int, typer.Option("--roi-y", help="ROI Y offset", rich_help_panel="ROI")
    ] = 0,
    roi_width: Annotated[
        int, typer.Option("--roi-width", help="ROI width", rich_help_panel="ROI")
    ] = 1920,
    roi_height: Annotated[
        int, typer.Option("--roi-height", help="ROI height", rich_help_panel="ROI")
    ] = 1080,
    # HDR Metadata
    eotf: Annotated[
        EOTFType,
        typer.Option(
            "--eotf", help="EOTF type (CEA 861.3)", rich_help_panel="HDR Metadata"
        ),
    ] = EOTFType.PQ,
    max_display_mastering_luminance: Annotated[
        float,
        typer.Option(
            "--max-display-mastering-luminance",
            help="Max display mastering luminance in cd/m²",
            rich_help_panel="HDR Metadata",
        ),
    ] = 1000.0,
    min_display_mastering_luminance: Annotated[
        float,
        typer.Option(
            "--min-display-mastering-luminance",
            help="Min display mastering luminance in cd/m²",
            rich_help_panel="HDR Metadata",
        ),
    ] = 0.0,
    max_cll: Annotated[
        float,
        typer.Option(
            "--max-cll",
            help="Maximum Content Light Level in cd/m²",
            rich_help_panel="HDR Metadata",
        ),
    ] = 10000.0,
    max_fall: Annotated[
        float,
        typer.Option(
            "--max-fall",
            help="Maximum Frame Average Light Level in cd/m²",
            rich_help_panel="HDR Metadata",
        ),
    ] = 80.0,
    red_primary: Annotated[
        tuple[float, float],
        typer.Option(
            "--red-primary",
            help="Red primary coordinates (x,y)",
            rich_help_panel="HDR Metadata",
        ),
    ] = (0.708, 0.292),
    green_primary: Annotated[
        tuple[float, float],
        typer.Option(
            "--green-primary",
            help="Green primary coordinates (x,y)",
            rich_help_panel="HDR Metadata",
        ),
    ] = (0.170, 0.797),
    blue_primary: Annotated[
        tuple[float, float],
        typer.Option(
            "--blue-primary",
            help="Blue primary coordinates (x,y)",
            rich_help_panel="HDR Metadata",
        ),
    ] = (0.131, 0.046),
    white_primary: Annotated[
        tuple[float, float],
        typer.Option(
            "--white-primary",
            help="White point coordinates (x,y)",
            rich_help_panel="HDR Metadata",
        ),
    ] = (0.3127, 0.3290),
    no_hdr: Annotated[
        bool,
        typer.Option(
            "--no-hdr", help="Disable HDR metadata", rich_help_panel="HDR Metadata"
        ),
    ] = False,
) -> None:
    """
    BMD Pattern Generator - Configure device and HDR settings globally.

    This callback function captures all global device configuration including
    hardware settings, ROI configuration, and HDR metadata parameters.
    These settings are passed to pattern-specific subcommands via context.
    """
    # Store common settings in context for subcommands to access
    ctx.ensure_object(dict)
    ctx.obj["device_settings"] = DecklinkSettings(
        # Device params
        device=device,
        pixel_format=pixel_format,
        width=width,
        height=height,
        # ROI params
        roi_x=roi_x,
        roi_y=roi_y,
        roi_width=roi_width,
        roi_height=roi_height,
        # HDR params
        eotf=eotf,
        max_cll=max_cll,
        max_fall=max_fall,
        max_display_mastering_luminance=max_display_mastering_luminance,
        min_display_mastering_luminance=min_display_mastering_luminance,
        red_primary=red_primary,
        green_primary=green_primary,
        blue_primary=blue_primary,
        white_point=white_primary,
        no_hdr=no_hdr,
    )


# Import and register commands
from bmd_sg.cli.commands.checkerboard_commands import (
    checkerboard2_command,
    checkerboard3_command,
    checkerboard4_command,
)
from bmd_sg.cli.commands.device_details import device_details_command
from bmd_sg.cli.commands.solid import solid_command

app.command(name="solid")(solid_command)
app.command(name="pat2")(checkerboard2_command)
app.command(name="pat3")(checkerboard3_command)
app.command(name="pat4")(checkerboard4_command)
app.command(name="device-details")(device_details_command)


if __name__ == "__main__":
    app()
