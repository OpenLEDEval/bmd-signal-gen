#!/usr/bin/env python3
"""
Typer-based CLI for BMD Signal Generator with optional config file support.
Supports HDR metadata configuration including EOTF settings and pixel format selection.
"""

import time
from pathlib import Path
from typing import Annotated, Optional, Tuple

import typer
import yaml
from typer import Argument, Option

from bmd_sg.decklink.bmd_decklink import EOTFType
from bmd_sg.decklink_control import (
    cleanup_decklink_device,
    display_pattern,
    setup_decklink_device,
)
from bmd_sg.pattern_generator import PatternType
from bmd_sg.signal_generator import DeckLinkSettings, PatternSettings

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
        self.red_primary = (0.708, 0.292)
        self.green_primary = (0.170, 0.797)
        self.blue_primary = (0.131, 0.046)
        self.white_primary = (0.3127, 0.3290)

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
                    elif key in ["red_primary", "green_primary", "blue_primary", "white_primary"] and isinstance(
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


def validate_color(value: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """Validate RGB color values."""
    r, g, b = value
    if not all(0 <= val <= 4095 for val in [r, g, b]):
        raise typer.BadParameter("RGB values must be between 0 and 4095 for 12-bit")
    return (r, g, b)


@app.command()
def pat2(
    # Colors
    color1: Annotated[
        Tuple[int, int, int],
        Argument(help="First color RGB values (r,g,b) - each 0-4095 for 12-bit"),
    ] = (4095, 4095, 4095),
    color2: Annotated[
        Tuple[int, int, int],
        Option(
            "--color2", 
            help="Second color RGB values (r,g,b) - each 0-4095 for 12-bit",
            rich_help_panel="Colors"
        ),
    ] = (0, 0, 0),
    
    # Basic Settings
    config: Annotated[
        Optional[Path], 
        Option(
            "--config", "-c", 
            help="Path to YAML config file",
            rich_help_panel="Basic Settings"
        )
    ] = None,
    duration: Annotated[
        float, 
        Option(
            "--duration", "-t", 
            help="Duration in seconds",
            rich_help_panel="Basic Settings"
        )
    ] = 5,
    
    # Device / Pixel Format
    device: Annotated[
        int, 
        Option(
            "--device", "-d", 
            help="Device index",
            rich_help_panel="Device / Pixel Format"
        )
    ] = 0,
    pixel_format: Annotated[
        Optional[int],
        Option(
            "--pixel-format",
            "-p",
            help="Pixel format index (auto-select if not specified)",
            rich_help_panel="Device / Pixel Format",
        ),
    ] = None,
    width: Annotated[
        int, 
        Option(
            "--width", 
            help="Image width",
            rich_help_panel="Device / Pixel Format"
        )
    ] = 1920,
    height: Annotated[
        int, 
        Option(
            "--height", 
            help="Image height",
            rich_help_panel="Device / Pixel Format"
        )
    ] = 1080,
    
    # ROI
    roi_x: Annotated[
        int, 
        Option(
            "--roi-x", 
            help="ROI X offset",
            rich_help_panel="ROI"
        )
    ] = 0,
    roi_y: Annotated[
        int, 
        Option(
            "--roi-y", 
            help="ROI Y offset",
            rich_help_panel="ROI"
        )
    ] = 0,
    roi_width: Annotated[
        int, 
        Option(
            "--roi-width", 
            help="ROI width",
            rich_help_panel="ROI"
        )
    ] = 1920,
    roi_height: Annotated[
        int, 
        Option(
            "--roi-height", 
            help="ROI height",
            rich_help_panel="ROI"
        )
    ] = 1080,
    
    # HDR Metadata
    eotf: Annotated[
        EOTFType,
        Option(
            "--eotf", 
            help="EOTF type (CEA 861.3)",
            rich_help_panel="HDR Metadata"
        ),
    ] = EOTFType.PQ,
    max_display_mastering_luminance: Annotated[
        float,
        Option(
            "--max-display-mastering-luminance",
            help="Max display mastering luminance in cd/m²",
            rich_help_panel="HDR Metadata",
        ),
    ] = 1000.0,
    min_display_mastering_luminance: Annotated[
        float,
        Option(
            "--min-display-mastering-luminance",
            help="Min display mastering luminance in cd/m²",
            rich_help_panel="HDR Metadata",
        ),
    ] = 0.0001,
    max_cll: Annotated[
        float, 
        Option(
            "--max-cll", 
            help="Maximum Content Light Level in cd/m²",
            rich_help_panel="HDR Metadata"
        )
    ] = 10000.0,
    max_fall: Annotated[
        float, 
        Option(
            "--max-fall", 
            help="Maximum Frame Average Light Level in cd/m²",
            rich_help_panel="HDR Metadata"
        )
    ] = 400.0,
    red_primary: Annotated[
        Tuple[float, float], 
        Option(
            "--red-primary", 
            help="Red primary coordinates (x,y)",
            rich_help_panel="HDR Metadata"
        )
    ] = (0.708, 0.292),
    green_primary: Annotated[
        Tuple[float, float], 
        Option(
            "--green-primary", 
            help="Green primary coordinates (x,y)",
            rich_help_panel="HDR Metadata"
        )
    ] = (0.170, 0.797),
    blue_primary: Annotated[
        Tuple[float, float], 
        Option(
            "--blue-primary", 
            help="Blue primary coordinates (x,y)",
            rich_help_panel="HDR Metadata"
        )
    ] = (0.131, 0.046),
    white_primary: Annotated[
        Tuple[float, float], 
        Option(
            "--white-primary", 
            help="White point coordinates (x,y)",
            rich_help_panel="HDR Metadata"
        )
    ] = (0.3127, 0.3290),
    no_hdr: Annotated[
        bool, 
        Option(
            "--no-hdr", 
            help="Disable HDR metadata",
            rich_help_panel="HDR Metadata"
        )
    ] = False,
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
    if red_primary != (0.708, 0.292):
        cfg.red_primary = red_primary
    if green_primary != (0.170, 0.797):
        cfg.green_primary = green_primary
    if blue_primary != (0.131, 0.046):
        cfg.blue_primary = blue_primary
    if white_primary != (0.3127, 0.3290):
        cfg.white_primary = white_primary
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

    # Create DeckLink settings
    decklink_settings = DeckLinkSettings(
        width=cfg.width,
        height=cfg.height,
        no_hdr=cfg.no_hdr,
        eotf=cfg.eotf,
        max_cll=cfg.max_cll,
        max_fall=cfg.max_fall,
        max_display_mastering_luminance=cfg.max_display_mastering_luminance,
        min_display_mastering_luminance=cfg.min_display_mastering_luminance,
        red_primary=cfg.red_primary,
        green_primary=cfg.green_primary,
        blue_primary=cfg.blue_primary,
        white_point=cfg.white_primary,
    )
    
    # Setup DeckLink device
    decklink, bit_depth, _ = setup_decklink_device(decklink_settings, cfg.device, cfg.pixel_format)
    if decklink is None:
        typer.echo("Failed to setup DeckLink device", err=True)
        raise typer.Exit(1)

    # Create pattern settings
    pattern_settings = PatternSettings(
        pattern=cfg.pattern,
        colors=[(cfg.color1[0], cfg.color1[1], cfg.color1[2]),
                (cfg.color2[0], cfg.color2[1], cfg.color2[2])],
        bit_depth=bit_depth or 12,  # Default to 12-bit if None
        width=cfg.width,
        height=cfg.height,
        roi_x=cfg.roi_x,
        roi_y=cfg.roi_y,
        roi_width=cfg.roi_width,
        roi_height=cfg.roi_height,
    )
    
    # Generate and display image
    success = display_pattern(pattern_settings, decklink)
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
            self.red_primary = (0.708, 0.292)
            self.green_primary = (0.170, 0.797)
            self.blue_primary = (0.131, 0.046)
            self.white_primary = (0.3127, 0.3290)
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
red_primary: [0.708, 0.292]
green_primary: [0.170, 0.797]
blue_primary: [0.131, 0.046]
white_primary: [0.3127, 0.3290]

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
    app()
