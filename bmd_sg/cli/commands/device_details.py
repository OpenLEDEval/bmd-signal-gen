"""
Device details command for BMD CLI.

This module provides the device details command that shows information
about all connected DeckLink devices including supported formats and HDR capabilities.
"""

from typing import Annotated

import typer

from bmd_sg.decklink.bmd_decklink import (
    BMDDeckLink,
    get_decklink_devices,
    get_decklink_driver_version,
    get_decklink_sdk_version,
)


def _print_system_info() -> None:
    """Print DeckLink system information."""
    typer.echo("DeckLink System Information:")
    typer.echo(f"  SDK Version: {get_decklink_sdk_version()}")
    typer.echo(f"  Driver Version: {get_decklink_driver_version()}")
    typer.echo()


def _print_device_details(idx: int, device_name: str) -> None:
    """Print detailed information for a specific device."""
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

    except RuntimeError as e:
        typer.echo(f"  Error accessing device: {e}")

    typer.echo()  # Empty line between devices


def device_details_command(
    device_index: Annotated[
        int | None,
        typer.Option(
            "--device",
            "-d",
            help="Show details for specific device index only",
        ),
    ] = None,
    list_only: Annotated[
        bool,
        typer.Option(
            "--list",
            "-l",
            help="Only show device names and indices",
        ),
    ] = False,
) -> None:
    """
    Show details for connected DeckLink devices.

    This command displays comprehensive information about the DeckLink system
    including SDK/driver versions and detailed information for connected
    devices such as supported pixel formats and HDR capabilities.

    The command does not require any global device settings as it operates
    independently to enumerate and inspect all available devices.

    Parameters
    ----------
    device_index : int | None
        Optional device index to show details for specific device only.
        If not specified, shows details for all devices.
    list_only : bool
        If True, only shows device names and indices without detailed
        format and HDR information.

    Output includes:
    - DeckLink SDK and driver version information (unless list_only)
    - List of connected devices with indices
    - Supported pixel formats for each device (unless list_only)
    - HDR support status for each device (unless list_only)

    Examples
    --------
    Show all device information:
    >>> bmd-cli device-details

    Show only device list:
    >>> bmd-cli device-details --list

    Show details for specific device:
    >>> bmd-cli device-details --device 1

    Show only specific device name:
    >>> bmd-cli device-details --device 0 --list

    Notes
    -----
    This command uses the BMDDeckLink context manager to safely open
    and close device connections during inspection. If a device cannot
    be accessed, an error message is displayed but enumeration continues
    for other devices.

    Raises
    ------
    typer.Exit
        If device enumeration fails completely or specified device index
        is out of range
    """
    try:
        # Get all available devices
        devices = get_decklink_devices()
        if not devices:
            typer.echo("No DeckLink devices found.")
            return

        # Validate device_index if specified
        if device_index is not None and (
            device_index < 0 or device_index >= len(devices)
        ):
            typer.echo(
                f"Error: Device index {device_index} is out of range (0-{len(devices) - 1})",
                err=True,
            )
            raise typer.Exit(1)

        # Print SDK and driver version information (unless list_only)
        if not list_only:
            _print_system_info()

        # Determine which devices to process
        if device_index is not None:
            devices_to_process = [(device_index, devices[device_index])]
            if not list_only:
                typer.echo(f"Device {device_index} details:\n")
        else:
            devices_to_process = list(enumerate(devices))
            if list_only:
                typer.echo(f"Found {len(devices)} DeckLink device(s):")
            else:
                typer.echo(f"Found {len(devices)} DeckLink device(s):\n")

        # Iterate through selected devices
        for idx, device_name in devices_to_process:
            if list_only:
                typer.echo(f"Device {idx}: {device_name}")
            else:
                _print_device_details(idx, device_name)

    except Exception as e:
        typer.echo(f"Error enumerating devices: {e}", err=True)
        raise typer.Exit(1) from e


__all__ = ["device_details_command"]
