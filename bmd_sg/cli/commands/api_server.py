"""
API server command for BMD CLI.

This module provides the CLI command to start the FastAPI server while
maintaining device configuration from the global CLI callback. The server
inherits all device settings and initializes persistent device state for
real-time pattern updates via HTTP API.
"""

import ipaddress
from typing import Annotated

import typer
import uvicorn

from bmd_sg.api.device_manager import device_manager
from bmd_sg.cli.shared import setup_tools_from_context


def _validate_host_security(host: str) -> None:
    """
    Validate host binding and issue security warnings for non-local addresses.

    This function checks if the provided host address is a local/loopback address
    or if it exposes the API to the network. Strong warnings are issued for
    network-exposed bindings to alert users about potential security risks.

    Parameters
    ----------
    host : str
        The host address to validate (e.g., '127.0.0.1', '0.0.0.0', '192.168.1.100')

    Notes
    -----
    Safe local addresses (no warning issued):
    - 127.0.0.1 (IPv4 loopback)
    - ::1 (IPv6 loopback)
    - localhost (hostname)

    Network-exposed addresses (warnings issued):
    - 0.0.0.0 (bind to all IPv4 interfaces)
    - :: (bind to all IPv6 interfaces)
    - Any specific network IP address

    Examples
    --------
    >>> _validate_host_security('127.0.0.1')  # No warning
    >>> _validate_host_security('0.0.0.0')    # Strong warning about network exposure
    >>> _validate_host_security('192.168.1.100')  # Warning with specific IP
    """
    # Handle common hostname cases first
    if host.lower() == "localhost":
        return  # Safe local binding

    try:
        # Parse the IP address
        ip_addr = ipaddress.ip_address(host)

        # Check if it's a loopback address (127.0.0.1, ::1)
        if ip_addr.is_loopback:
            return  # Safe local binding

        # Check for bind-to-all addresses (0.0.0.0, ::)
        if ip_addr.is_unspecified:
            typer.echo(
                "⚠️  WARNING: Binding to all interfaces exposes API to network!",
                err=True,
            )
            typer.echo(
                "   This makes the API accessible from other machines on the network.",
                err=True,
            )
            typer.echo(
                "   Use 127.0.0.1 or localhost for local-only access.",
                err=True,
            )
            return

        # Any other IP address is potentially network-exposed
        typer.echo(
            f"⚠️  WARNING: Binding to network IP {host} exposes API to network!",
            err=True,
        )
        typer.echo(
            "   This makes the API accessible from other machines.",
            err=True,
        )
        typer.echo(
            "   Use 127.0.0.1 or localhost for local-only access.",
            err=True,
        )

    except ValueError:
        # Invalid IP address format - let uvicorn handle the error
        typer.echo(
            f"⚠️  WARNING: Invalid host address format: {host}",
            err=True,
        )
        typer.echo(
            "   Server may fail to start with invalid host address.",
            err=True,
        )


def api_server_command(
    ctx: typer.Context,
    host: Annotated[
        str,
        typer.Option(
            "--host",
            "-h",
            help="Host address to bind the API server",
        ),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option(
            "--port",
            "-p",
            help="Port number for the API server",
        ),
    ] = 4844,
    reload: Annotated[
        bool,
        typer.Option(
            "--reload",
            help="Enable auto-reload for development",
        ),
    ] = False,
) -> None:
    """
    Start FastAPI server with current device configuration.

    This command initializes the API server using the global device settings
    from the CLI callback (device index, pixel format, resolution, HDR metadata).
    The server provides HTTP endpoints for real-time pattern updates while
    maintaining persistent device state.

    The API server supports the following endpoints:
    - POST /update_color: Update pattern colors (1-4 colors)
    - GET /status: Get device and pattern status
    - GET /health: Health check endpoint
    - GET /docs: OpenAPI documentation

    All device configuration (resolution, HDR metadata, etc.) is inherited from
    the global CLI settings and cannot be changed while the server is running.

    Parameters
    ----------
    ctx : typer.Context
        Typer context containing global device settings
    host : str
        Host address to bind the API server (default: 127.0.0.1)
    port : int
        Port number for the API server (default: 4844)
    reload : bool
        Enable auto-reload for development (default: False)

    Examples
    --------
    Start API server with default settings:
    >>> bmd-cli api-server

    Start server on all interfaces with custom port:
    >>> bmd-cli api-server --host 0.0.0.0 --port 8080

    Start with device configuration:
    >>> bmd-cli --device 1 --width 3840 --height 2160 api-server

    Start with HDR configuration:
    >>> bmd-cli --eotf PQ --max-cll 10000 api-server --port 9000

    Development mode with auto-reload:
    >>> bmd-cli api-server --reload

    Notes
    -----
    The server will initialize the DeckLink device using the same workflow
    as pattern commands (setup_tools_from_context). Device errors during
    initialization will prevent the server from starting.

    The API endpoints accept color values in the same range as CLI commands:
    - 12-bit: 0-4095 (default, recommended)
    - 10-bit: 0-1023
    - 8-bit:  0-255 (fallback)

    Press Ctrl+C to stop the server and clean up device resources.

    Raises
    ------
    RuntimeError
        If device setup fails (passed through from setup_tools_from_context)
    typer.Exit
        If device initialization fails or server startup errors

    See Also
    --------
    bmd_sg.api.main : FastAPI application implementation
    bmd_sg.api.device_manager : Device state management
    bmd_sg.cli.shared.setup_tools_from_context : Device initialization
    """
    try:
        typer.echo("🔧 Initializing DeckLink device from CLI settings...")

        # Initialize device using existing CLI workflow
        decklink, generator = setup_tools_from_context(ctx)

        # Get device settings for the API
        settings = ctx.obj["device_settings"]

        typer.echo(
            f"✅ Device initialized: {getattr(decklink, 'device_name', 'Unknown')}"
        )
        typer.echo(f"📐 Resolution: {settings.width}x{settings.height}")
        typer.echo(f"🎨 Pixel format: {settings.pixel_format or 'Auto'}")
        typer.echo(f"🌈 HDR enabled: {not settings.no_hdr}")

        # Initialize the global device manager
        device_manager.initialize(decklink, generator, settings)

        # Validate host security before startup
        _validate_host_security(host)

        typer.echo("🚀 Starting FastAPI server...")
        typer.echo(f"🌐 Server URL: http://{host}:{port}")
        typer.echo(f"📖 API docs: http://{host}:{port}/docs")
        typer.echo("💡 Press Ctrl+C to stop the server")

        # Start the FastAPI server
        uvicorn.run(
            "bmd_sg.api.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info",
        )

    except KeyboardInterrupt:
        typer.echo("\n🛑 Server stopped by user")
        raise typer.Exit(0) from None

    except Exception as e:
        typer.echo(f"❌ Failed to start API server: {e!s}", err=True)
        raise typer.Exit(1) from e


__all__ = ["api_server_command"]
