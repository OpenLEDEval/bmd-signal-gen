"""
Device details command for BMD CLI.

This module provides the device details command that shows information
about all connected DeckLink devices including supported formats and HDR capabilities.
"""

import typer

from bmd_sg.decklink.bmd_decklink import (
    BMDDeckLink,
    get_decklink_devices,
    get_decklink_driver_version,
    get_decklink_sdk_version,
)


def device_details_command() -> None:
    """
    Show details for all connected DeckLink devices.

    This command displays comprehensive information about the DeckLink system
    including SDK/driver versions and detailed information for each connected
    device such as supported pixel formats and HDR capabilities.

    The command does not require any global device settings as it operates
    independently to enumerate and inspect all available devices.

    Output includes:
    - DeckLink SDK and driver version information
    - List of all connected devices with indices
    - Supported pixel formats for each device
    - HDR support status for each device

    Examples
    --------
    Show all device information:
    >>> bmd-cli device-details

    Notes
    -----
    This command uses the BMDDeckLink context manager to safely open
    and close device connections during inspection. If a device cannot
    be accessed, an error message is displayed but enumeration continues
    for other devices.

    Raises
    ------
    typer.Exit
        If device enumeration fails completely
    """
    try:
        # Print SDK and driver version information first
        typer.echo("DeckLink System Information:")
        typer.echo(f"  SDK Version: {get_decklink_sdk_version()}")
        typer.echo(f"  Driver Version: {get_decklink_driver_version()}")
        typer.echo()

        # Get all available devices
        devices = get_decklink_devices()
        if not devices:
            typer.echo("No DeckLink devices found.")
            return

        typer.echo(f"Found {len(devices)} DeckLink device(s):\n")

        # Iterate through each device
        for idx, device_name in enumerate(devices):
            typer.echo(f"Device {idx}: {device_name}")
            try:
                # Open the device to get its details using context manager
                with BMDDeckLink(device_index=idx) as decklink:
                    # Get supported pixel formats
                    formats = decklink.get_supported_pixel_formats()
                    typer.echo(f"  Supported pixel formats ({len(formats)}):")
                    for format_idx, pixel_format in enumerate(formats):
                        typer.echo(
                            f"    {format_idx}: {pixel_format.name} ({pixel_format.bit_depth}-bit)"
                        )

                    # Check HDR support
                    hdr_support = decklink.supports_hdr
                    typer.echo(f"  HDR Support: {'Yes' if hdr_support else 'No'}")

                    # Device automatically closed when exiting with block

            except RuntimeError as e:
                typer.echo(f"  Error accessing device: {e}")

            typer.echo()  # Empty line between devices

    except Exception as e:
        typer.echo(f"Error enumerating devices: {e}", err=True)
        raise typer.Exit(1) from e
