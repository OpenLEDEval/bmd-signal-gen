"""
Solid color pattern command for BMD CLI.

This module provides the solid color pattern generation command that inherits
global device settings from the main CLI callback.
"""

from typing import Annotated

import typer

from bmd_sg.cli.shared import (
    display_image_for_duration,
    setup_tools_from_context,
    validate_color,
)


def solid_command(
    ctx: typer.Context,
    # Pattern-specific parameters only
    color: Annotated[
        tuple[int, int, int],
        typer.Argument(help="RGB color values (r,g,b) - each 0-4095 for 12-bit"),
    ] = (2081, 2081, 2081),
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
    Generate and display solid color pattern.

    This command generates a solid color pattern using the specified RGB values.
    All device configuration (resolution, HDR metadata, etc.) is inherited from
    the global CLI settings.

    The pattern creates a uniform color across the entire output frame or within
    the specified ROI. This is useful for testing display uniformity, measuring
    luminance levels, and calibrating color accuracy.

    Color value ranges by pixel format:
    - 12-bit: 0-4095 (default, recommended)
    - 10-bit: 0-1023
    - 8-bit:  0-255 (fallback mode)

    Parameters
    ----------
    ctx : typer.Context
        Typer context containing global device settings
    color : tuple[int, int, int]
        RGB color values as tuple (red, green, blue)
    duration : float
        Display duration in seconds

    Raises
    ------
    typer.BadParameter
        If color values are outside the valid range (0-4095 for 12-bit)
    RuntimeError
        If device setup fails (passed through from setup_tools_from_context)

    Examples
    --------
    Generate white pattern for 10 seconds:
    >>> bmd-cli solid 4095 4095 4095 --duration 10

    Generate red pattern with device settings:
    >>> bmd-cli --device 1 --width 3840 solid 4095 0 0

    Generate 50% gray pattern:
    >>> bmd-cli solid 2048 2048 2048

    See Also
    --------
    checkerboard2 : Two-color checkerboard patterns
    checkerboard3 : Three-color checkerboard patterns
    checkerboard4 : Four-color checkerboard patterns
    """
    # Setup device and generator using global settings from context
    decklink, generator = setup_tools_from_context(ctx)

    # Validate color values using device bit depth
    validated_color = validate_color(color, decklink)

    # Generate solid color pattern
    pattern = generator.generate([validated_color])

    # Display the pattern for specified duration
    display_image_for_duration(decklink, pattern, duration)


__all__ = ["solid_command"]
