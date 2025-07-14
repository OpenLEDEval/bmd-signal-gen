"""
Checkerboard pattern commands for BMD CLI.

This module provides multiple checkerboard pattern commands that generate 2, 3, and 4-color
checkerboard patterns with configurable colors. All commands inherit global device settings
from the main CLI callback including resolution, HDR metadata, and device configuration.

Available commands:
- checkerboard2_command: Two-color checkerboard patterns
- checkerboard3_command: Three-color checkerboard patterns
- checkerboard4_command: Four-color checkerboard patterns
"""

from typing import Annotated

import typer

from bmd_sg.cli.shared import (
    display_image_for_duration,
    setup_tools_from_context,
    validate_color,
)


def checkerboard2_command(
    ctx: typer.Context,
    # Pattern-specific parameters only
    color1: Annotated[
        tuple[int, int, int],
        typer.Argument(help="First color RGB values (r,g,b) - each 0-4095 for 12-bit"),
    ] = (2081, 2081, 2081),
    color2: Annotated[
        tuple[int, int, int],
        typer.Option(
            "--color2",
            help="Second color RGB values (r,g,b) - each 0-4095 for 12-bit",
        ),
    ] = (0, 0, 0),
    duration: Annotated[
        float,
        typer.Option(
            "--duration",
            "-t",
            help="Duration in seconds",
        ),
    ] = 5.0,
) -> None:
    """
    Generate and display two-color checkerboard pattern.

    This command generates a two-color checkerboard pattern using the specified RGB values.
    All device configuration (resolution, HDR metadata, etc.) is inherited from
    the global CLI settings.

    The pattern creates a checkerboard using the first color (color1) and second color (color2)
    in alternating squares. This is useful for testing display uniformity, pixel response,
    and color accuracy across different areas of the screen.

    Color value ranges by pixel format:
    - 12-bit: 0-4095 (default, recommended)
    - 10-bit: 0-1023
    - 8-bit:  0-255 (fallback mode)

    Parameters
    ----------
    ctx : typer.Context
        Typer context containing global device settings
    color1 : tuple[int, int, int]
        First checkerboard color as RGB tuple (primary squares)
    color2 : tuple[int, int, int]
        Second checkerboard color as RGB tuple (alternate squares)
    duration : float
        Display duration in seconds

    Examples
    --------
    Generate white/black checkerboard for 10 seconds:
    >>> bmd-cli checkerboard2 4095 4095 4095 --color2 0 0 0 --duration 10

    Generate red/blue checkerboard with device settings:
    >>> bmd-cli --device 1 --width 3840 checkerboard2 4095 0 0 --color2 0 0 4095

    Generate 50% gray checkerboard:
    >>> bmd-cli checkerboard2 2048 2048 2048 --color2 1024 1024 1024

    Notes
    -----
    The checkerboard pattern uses the PatternGenerator with a two-color list.
    The pattern generator automatically creates alternating squares with the
    provided colors. Square size is determined by the pattern generator's
    internal algorithm.

    Raises
    ------
    typer.BadParameter
        If color values are outside the valid range (0-4095 for 12-bit)
    RuntimeError
        If device setup fails (passed through from setup_tools_from_context)

    See Also
    --------
    solid : Single solid color patterns
    checkerboard3 : Three-color checkerboard patterns
    checkerboard4 : Four-color checkerboard patterns
    """
    # Setup device and generator using global settings from context
    decklink, generator = setup_tools_from_context(ctx)

    # Validate color values using device bit depth
    validated_colors = validate_color([color1, color2], decklink)

    # Generate two-color checkerboard pattern
    pattern = generator.generate(validated_colors)

    # Display the pattern for specified duration
    display_image_for_duration(decklink, pattern, duration)


def checkerboard3_command(
    ctx: typer.Context,
    # Pattern-specific parameters only
    color1: Annotated[
        tuple[int, int, int],
        typer.Argument(help="First color RGB values (r,g,b) - each 0-4095 for 12-bit"),
    ] = (0, 2372, 0),
    color2: Annotated[
        tuple[int, int, int],
        typer.Option(
            "--color2",
            help="Second color RGB values (r,g,b) - each 0-4095 for 12-bit",
        ),
    ] = (2372, 0, 0),
    color3: Annotated[
        tuple[int, int, int],
        typer.Option(
            "--color3",
            help="Third color RGB values (r,g,b) - each 0-4095 for 12-bit",
        ),
    ] = (0, 0, 2372),
    duration: Annotated[
        float,
        typer.Option(
            "--duration",
            "-t",
            help="Duration in seconds",
        ),
    ] = 5.0,
) -> None:
    """
    Generate and display three-color checkerboard pattern.

    This command generates a three-color checkerboard pattern using the specified RGB values.
    All device configuration (resolution, HDR metadata, etc.) is inherited from
    the global CLI settings.

    The pattern creates a checkerboard using three colors arranged according to the
    pattern generator's three-color mapping: [color1, color2, color3, color1].
    This creates a pattern where color1 appears in top-left and bottom-right squares,
    color2 in top-right, and color3 in bottom-left.

    Color value ranges by pixel format:
    - 12-bit: 0-4095 (default, recommended)
    - 10-bit: 0-1023
    - 8-bit:  0-255 (fallback mode)

    Parameters
    ----------
    ctx : typer.Context
        Typer context containing global device settings
    color1 : tuple[int, int, int]
        First checkerboard color as RGB tuple (top-left and bottom-right squares)
    color2 : tuple[int, int, int]
        Second checkerboard color as RGB tuple (top-right square)
    color3 : tuple[int, int, int]
        Third checkerboard color as RGB tuple (bottom-left square)
    duration : float
        Display duration in seconds

    Examples
    --------
    Generate white/black/gray checkerboard for 10 seconds:
    >>> bmd-cli checkerboard3 4095 4095 4095 --color2 0 0 0 --color3 2048 2048 2048 --duration 10

    Generate red/green/blue checkerboard with device settings:
    >>> bmd-cli --device 1 --width 3840 checkerboard3 4095 0 0 --color2 0 4095 0 --color3 0 0 4095

    Generate neutral test pattern:
    >>> bmd-cli checkerboard3 3000 3000 3000 --color2 1500 1500 1500 --color3 500 500 500

    Notes
    -----
    The checkerboard pattern uses the PatternGenerator with a three-color list.
    The pattern generator maps the three colors to create a visually balanced
    test pattern useful for display calibration and uniformity testing.

    Raises
    ------
    typer.BadParameter
        If color values are outside the valid range (0-4095 for 12-bit)
    RuntimeError
        If device setup fails (passed through from setup_tools_from_context)

    See Also
    --------
    solid : Single solid color patterns
    checkerboard2 : Two-color checkerboard patterns
    checkerboard4 : Four-color checkerboard patterns
    """
    # Setup device and generator using global settings from context
    decklink, generator = setup_tools_from_context(ctx)

    # Validate color values using device bit depth
    validated_colors = validate_color([color1, color2, color3], decklink)

    # Generate three-color checkerboard pattern
    pattern = generator.generate(validated_colors)

    # Display the pattern for specified duration
    display_image_for_duration(decklink, pattern, duration)


def checkerboard4_command(
    ctx: typer.Context,
    # Pattern-specific parameters only
    color1: Annotated[
        tuple[int, int, int],
        typer.Argument(help="First color RGB values (r,g,b) - each 0-4095 for 12-bit"),
    ] = (2372, 0, 0),
    color2: Annotated[
        tuple[int, int, int],
        typer.Option(
            "--color2",
            help="Second color RGB values (r,g,b) - each 0-4095 for 12-bit",
        ),
    ] = (0, 2372, 0),
    color3: Annotated[
        tuple[int, int, int],
        typer.Option(
            "--color3",
            help="Third color RGB values (r,g,b) - each 0-4095 for 12-bit",
        ),
    ] = (0, 0, 2372),
    color4: Annotated[
        tuple[int, int, int],
        typer.Option(
            "--color4",
            help="Fourth color RGB values (r,g,b) - each 0-4095 for 12-bit",
        ),
    ] = (2372, 2372, 0),
    duration: Annotated[
        float,
        typer.Option(
            "--duration",
            "-t",
            help="Duration in seconds",
        ),
    ] = 5.0,
) -> None:
    """
    Generate and display four-color checkerboard pattern.

    This command generates a four-color checkerboard pattern using the specified RGB values.
    All device configuration (resolution, HDR metadata, etc.) is inherited from
    the global CLI settings.

    The pattern creates a true 2x2 checkerboard using all four colors arranged as:
    - Top-left: color1
    - Top-right: color2
    - Bottom-left: color3
    - Bottom-right: color4

    This provides maximum flexibility for creating complex test patterns useful for
    display calibration, color accuracy testing, and uniformity evaluation.

    Color value ranges by pixel format:
    - 12-bit: 0-4095 (default, recommended)
    - 10-bit: 0-1023
    - 8-bit:  0-255 (fallback mode)

    Parameters
    ----------
    ctx : typer.Context
        Typer context containing global device settings
    color1 : tuple[int, int, int]
        First checkerboard color as RGB tuple (top-left squares)
    color2 : tuple[int, int, int]
        Second checkerboard color as RGB tuple (top-right squares)
    color3 : tuple[int, int, int]
        Third checkerboard color as RGB tuple (bottom-left squares)
    color4 : tuple[int, int, int]
        Fourth checkerboard color as RGB tuple (bottom-right squares)
    duration : float
        Display duration in seconds

    Examples
    --------
    Generate white/black/red/green checkerboard for 10 seconds:
    >>> bmd-cli checkerboard4 4095 4095 4095 --color2 0 0 0 --color3 4095 0 0 --color4 0 4095 0 --duration 10

    Generate grayscale gradient checkerboard:
    >>> bmd-cli checkerboard4 4095 4095 4095 --color2 2731 2731 2731 --color3 1365 1365 1365 --color4 0 0 0

    Generate RGBW test pattern with device settings:
    >>> bmd-cli --device 1 --width 3840 checkerboard4 4095 0 0 --color2 0 4095 0 --color3 0 0 4095 --color4 4095 4095 4095

    Notes
    -----
    The checkerboard pattern uses the PatternGenerator with a four-color list,
    providing direct control over each quadrant of the repeating checkerboard tile.
    This is ideal for complex display testing scenarios requiring precise color
    placement and comparison.

    Raises
    ------
    typer.BadParameter
        If color values are outside the valid range (0-4095 for 12-bit)
    RuntimeError
        If device setup fails (passed through from setup_tools_from_context)

    See Also
    --------
    solid : Single solid color patterns
    checkerboard2 : Two-color checkerboard patterns
    checkerboard3 : Three-color checkerboard patterns
    """
    # Setup device and generator using global settings from context
    decklink, generator = setup_tools_from_context(ctx)

    # Validate color values using device bit depth
    validated_colors = validate_color([color1, color2, color3, color4], decklink)

    # Generate four-color checkerboard pattern
    pattern = generator.generate(validated_colors)

    # Display the pattern for specified duration
    display_image_for_duration(decklink, pattern, duration)


__all__ = [
    "checkerboard2_command",
    "checkerboard3_command",
    "checkerboard4_command",
]
