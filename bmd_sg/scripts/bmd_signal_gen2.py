#!/usr/bin/env python3
"""
Typer-based CLI for BMD Signal Generator with optional config file support.
Supports HDR metadata configuration including EOTF settings and pixel format selection.
"""

import sys
import time
from pathlib import Path
from typing import Annotated, Optional, Tuple

import typer
import yaml
from typer import Argument, Option

from bmd_sg.decklink.bmd_decklink import EOTFType
from bmd_sg.decklink_control import (
    cleanup_decklink_device,
    generate_and_display_image,
    setup_decklink_device,
)
from bmd_sg.patterns import PatternType

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="BMD Signal Generator - Output test patterns to Blackmagic Design DeckLink devices",
)


class Config:
    """Configuration container for CLI arguments."""

    def __init__(self, config_file: Optional[Path] = None):
        # Default values
        self.color1 = (4095, 0, 0)
        self.color2 = (0, 0, 0)
        self.color3 = (0, 0, 0)
        self.color4 = (0, 0, 0)
        self.duration = 5.0
        self.device = 0
        self.pixel_format: Optional[int] = None
        self.eotf = EOTFType.PQ
        self.pattern = PatternType.TWO_COLOR
        self.width = 1920
        self.height = 1080

        # ROI settings
        self.roi_x = 64
        self.roi_y = 64
        self.roi_width = 64
        self.roi_height = 64

        # HDR metadata
        self.max_display_mastering_luminance = 1000.0
        self.min_display_mastering_luminance = 0.0001
        self.max_cll = 10000.0
        self.max_fall = 400.0

        # Color primaries (Rec2020 defaults)
        self.red = (0.708, 0.292)
        self.green = (0.170, 0.797)
        self.blue = (0.131, 0.046)
        self.white = (0.3127, 0.3290)

        self.no_hdr = False

        # Load from config file if provided
        if config_file:
            self.load_config(config_file)

    def load_config(self, config_file: Path):
        """Load configuration from YAML file."""
        if not config_file.exists():
            typer.echo(f"Config file not found: {config_file}", err=True)
            return

        try:
            with open(config_file, "r") as f:
                config_data = yaml.safe_load(f)

            if not config_data:
                return

            # Update attributes from config file
            for key, value in config_data.items():
                if hasattr(self, key):
                    # Handle special cases
                    if key == "eotf" and isinstance(value, str):
                        try:
                            self.eotf = EOTFType.parse(value)
                        except ValueError:
                            typer.echo(
                                f"Invalid EOTF value in config: {value}", err=True
                            )
                    elif key == "pattern" and isinstance(value, str):
                        try:
                            self.pattern = PatternType(value)
                        except ValueError:
                            typer.echo(
                                f"Invalid pattern value in config: {value}", err=True
                            )
                    elif key in ["red", "green", "blue", "white"] and isinstance(
                        value, list
                    ):
                        if len(value) == 2:
                            setattr(self, key, tuple(value))
                        else:
                            typer.echo(
                                f"Invalid chromaticity coordinates in config for {key}: {value}",
                                err=True,
                            )
                    elif key in ["color1", "color2", "color3", "color4"] and isinstance(
                        value, list
                    ):
                        if len(value) == 3:
                            setattr(self, key, tuple(value))
                        else:
                            typer.echo(
                                f"Invalid color RGB values in config for {key}: {value}",
                                err=True,
                            )
                    else:
                        setattr(self, key, value)
                else:
                    typer.echo(f"Unknown config option: {key}", err=True)

        except yaml.YAMLError as e:
            typer.echo(f"Error parsing config file: {e}", err=True)
        except Exception as e:
            typer.echo(f"Error loading config file: {e}", err=True)


def validate_chromaticity(value: str) -> Tuple[float, float]:
    """Validate chromaticity coordinates."""
    try:
        parts = value.split(",")
        if len(parts) != 2:
            raise typer.BadParameter("Chromaticity coordinates must be in format 'x,y'")

        x, y = float(parts[0]), float(parts[1])
        if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
            raise typer.BadParameter(
                "Chromaticity coordinates must be between 0.0 and 1.0"
            )

        return (x, y)
    except ValueError:
        raise typer.BadParameter("Chromaticity coordinates must be valid numbers")


def validate_color(value: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """Validate RGB color values."""
    r, g, b = value
    if not all(0 <= val <= 4095 for val in [r, g, b]):
        raise typer.BadParameter("RGB values must be between 0 and 4095 for 12-bit")
    return (r, g, b)


@app.command()
def pat2(
    # Basic color arguments
    color1: Annotated[
        Tuple[int, int, int],
        Argument(help="First color RGB values (r,g,b) - each 0-4095 for 12-bit"),
    ] = (4095, 4095, 4095),
    # Second color for 2-color pattern
    color2: Annotated[
        Tuple[int, int, int],
        Option(
            "--color2", help="Second color RGB values (r,g,b) - each 0-4095 for 12-bit"
        ),
    ] = (0, 0, 0),
    # Config file
    config: Annotated[
        Optional[Path], Option("--config", "-c", help="Path to YAML config file")
    ] = None,
    # Duration
    duration: Annotated[
        float, Option("--duration", "-t", help="Duration in seconds")
    ] = 0,
    # Device settings
    device: Annotated[int, Option("--device", "-d", help="Device index")] = 0,
    # Pattern settings
    width: Annotated[int, Option("--width", help="Image width")] = 1920,
    height: Annotated[int, Option("--height", help="Image height")] = 1080,
    # ROI settings
    roi_x: Annotated[int, Option("--roi-x", help="ROI X offset")] = 0,
    roi_y: Annotated[int, Option("--roi-y", help="ROI Y offset")] = 0,
    roi_width: Annotated[int, Option("--roi-width", help="ROI width")] = 1920,
    roi_height: Annotated[int, Option("--roi-height", help="ROI height")] = 1080,
    # HDR settings
    pixel_format: Annotated[
        Optional[int],
        Option(
            "--pixel-format",
            "-p",
            help="Pixel format index (auto-select if not specified)",
        ),
    ] = None,
    eotf: Annotated[
        EOTFType,
        Option("--eotf", help="EOTF type (CEA 861.3)"),
    ] = EOTFType.PQ,
    max_display_mastering_luminance: Annotated[
        float,
        Option(
            "--max-display-mastering-luminance",
            help="Max display mastering luminance in cd/m²",
        ),
    ] = 1000.0,
    min_display_mastering_luminance: Annotated[
        float,
        Option(
            "--min-display-mastering-luminance",
            help="Min display mastering luminance in cd/m²",
        ),
    ] = 0.0001,
    max_cll: Annotated[
        float, Option("--max-cll", help="Maximum Content Light Level in cd/m²")
    ] = 10000.0,
    max_fall: Annotated[
        float, Option("--max-fall", help="Maximum Frame Average Light Level in cd/m²")
    ] = 400.0,
    # Color primaries
    red: Annotated[
        str, Option("--red", help="Red primary coordinates 'x,y'")
    ] = "0.708,0.292",
    green: Annotated[
        str, Option("--green", help="Green primary coordinates 'x,y'")
    ] = "0.170,0.797",
    blue: Annotated[
        str, Option("--blue", help="Blue primary coordinates 'x,y'")
    ] = "0.131,0.046",
    white: Annotated[
        str, Option("--white", help="White point coordinates 'x,y'")
    ] = "0.3127,0.3290",
    # Flags
    no_hdr: Annotated[bool, Option("--no-hdr", help="Disable HDR metadata")] = False,
) -> None:
    """
    Generate and display test patterns on BMD DeckLink devices.

    Color value ranges by pixel format:
    - 12-bit: 0-4095 (default, recommended)
    - 10-bit: 0-1023
    - 8-bit:  0-255 (fallback mode)

    Pattern type: Two-color checkerboard

    Config file format (YAML):
    ```yaml
    r: 4095
    g: 0
    b: 0
    duration: 5.0
    pattern: "2color"
    eotf: "PQ"
    red: [0.708, 0.292]
    green: [0.170, 0.797]
    # ... etc
    ```
    """

    # Load config first, then override with CLI arguments
    cfg = Config(config)

    # Override config with CLI arguments (only if they differ from defaults)
    if color1 != (4095, 0, 0):
        cfg.color1 = validate_color(color1)
    if color2 != (0, 0, 0):
        cfg.color2 = validate_color(color2)
    if cfg.color3 != (0, 0, 0):
        cfg.color3 = validate_color(cfg.color3)
    if cfg.color4 != (0, 0, 0):
        cfg.color4 = validate_color(cfg.color4)

    if duration != 5.0:
        cfg.duration = duration
    if device != 0:
        cfg.device = device
    if pixel_format is not None:
        cfg.pixel_format = pixel_format
    # Pattern is always TWO_COLOR for pat2 command
    cfg.pattern = PatternType.TWO_COLOR
    if width != 1920:
        cfg.width = width
    if height != 1080:
        cfg.height = height
    if roi_x != 64:
        cfg.roi_x = roi_x
    if roi_y != 64:
        cfg.roi_y = roi_y
    if roi_width != 64:
        cfg.roi_width = roi_width
    if roi_height != 64:
        cfg.roi_height = roi_height
    if eotf != EOTFType.PQ:
        cfg.eotf = eotf
    if max_display_mastering_luminance != 1000.0:
        cfg.max_display_mastering_luminance = max_display_mastering_luminance
    if min_display_mastering_luminance != 0.0001:
        cfg.min_display_mastering_luminance = min_display_mastering_luminance
    if max_cll != 10000.0:
        cfg.max_cll = max_cll
    if max_fall != 400.0:
        cfg.max_fall = max_fall
    if red != "0.708,0.292":
        cfg.red = validate_chromaticity(red)
    if green != "0.170,0.797":
        cfg.green = validate_chromaticity(green)
    if blue != "0.131,0.046":
        cfg.blue = validate_chromaticity(blue)
    if white != "0.3127,0.3290":
        cfg.white = validate_chromaticity(white)
    if no_hdr:
        cfg.no_hdr = no_hdr

    # Convert config to argparse-like namespace for compatibility
    class Args:
        pass

    args = Args()
    for attr in dir(cfg):
        if not attr.startswith("_"):
            setattr(args, attr, getattr(cfg, attr))

    # Convert color tuples back to individual components for backward compatibility
    args.r, args.g, args.b = cfg.color1
    args.r2, args.g2, args.b2 = cfg.color2
    args.r3, args.g3, args.b3 = cfg.color3
    args.r4, args.g4, args.b4 = cfg.color4

    # Setup DeckLink device
    decklink, bit_depth, _ = setup_decklink_device(args)
    if decklink is None:
        typer.echo("Failed to setup DeckLink device", err=True)
        raise typer.Exit(1)

    # Generate and display image
    success = generate_and_display_image(args, decklink, bit_depth)
    if success:
        typer.echo(f"Displaying for {cfg.duration} seconds...")
        time.sleep(cfg.duration)

    # Cleanup
    cleanup_decklink_device(decklink)

    if not success:
        raise typer.Exit(1)


@app.command()
def list_formats(
    device: Annotated[int, Option("--device", "-d", help="Device index")] = 0,
) -> None:
    """List all supported pixel formats for the specified device."""

    # Create a minimal config for device setup
    class Args:
        def __init__(self):
            self.device = device
            self.all = True  # Enable listing all formats
            self.pixel_format = None
            self.eotf = EOTFType.PQ
            self.max_display_mastering_luminance = 1000.0
            self.min_display_mastering_luminance = 0.0001
            self.max_cll = 10000.0
            self.max_fall = 400.0
            self.red = (0.708, 0.292)
            self.green = (0.170, 0.797)
            self.blue = (0.131, 0.046)
            self.white = (0.3127, 0.3290)
            self.no_hdr = False

    args = Args()

    # Setup DeckLink device (this will list formats when all=True)
    decklink, bit_depth, _ = setup_decklink_device(args)
    if decklink is None:
        typer.echo("Failed to setup DeckLink device", err=True)
        raise typer.Exit(1)

    # Cleanup
    cleanup_decklink_device(decklink)


@app.command()
def config_template():
    """Generate a template config file."""
    template = """# BMD Signal Generator Configuration File
# All values are optional - CLI arguments will override these settings

# Color values (RGB tuples, each component 0-4095 for 12-bit)
color1: [4095, 0, 0]  # Red
color2: [0, 0, 0]     # Black
color3: [0, 0, 0]     # Black
color4: [0, 0, 0]     # Black

# Duration in seconds
duration: 5.0

# Device settings
device: 0
# pixel_format: null  # auto-select if not specified

# Pattern settings
# pattern is always 2color for pat2 command
width: 1920
height: 1080

# Region of Interest
roi_x: 64
roi_y: 64
roi_width: 64
roi_height: 64

# HDR settings
eotf: "PQ"  # SDR, PQ, HLG
max_display_mastering_luminance: 1000.0
min_display_mastering_luminance: 0.0001
max_cll: 10000.0
max_fall: 400.0

# Color primaries (Rec2020 defaults)
red: [0.708, 0.292]
green: [0.170, 0.797]
blue: [0.131, 0.046]
white: [0.3127, 0.3290]

# Flags
no_hdr: false
"""

    config_file = Path("bmd_signal_gen_config.yaml")
    if config_file.exists():
        overwrite = typer.confirm(
            f"Config file {config_file} already exists. Overwrite?"
        )
        if not overwrite:
            typer.echo("Config file generation cancelled.")
            return

    with open(config_file, "w") as f:
        f.write(template)

    typer.echo(f"Config template written to {config_file}")


if __name__ == "__main__":
    sys.argv = ["bmd_signal_gen2.py", "pat2", "--help"]
    app()
