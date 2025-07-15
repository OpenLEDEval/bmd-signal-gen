"""
FastAPI application for BMD Signal Generator API.

This module provides the main FastAPI application with endpoints for real-time
pattern updates, device status monitoring, and health checks. The application
integrates with the existing BMD device management infrastructure while
providing a stateful web interface.
"""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from bmd_sg.api.device_manager import device_manager
from bmd_sg.api.models import (
    ColorUpdateRequest,
    ColorUpdateResponse,
    DeviceStatusResponse,
    ErrorResponse,
    HealthResponse,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    FastAPI lifespan context manager.

    Manages application startup and shutdown lifecycle, ensuring proper
    device resource cleanup when the API server terminates.

    Parameters
    ----------
    app : FastAPI
        The FastAPI application instance

    Yields
    ------
    None
        Control during application runtime

    Notes
    -----
    Device initialization is handled by the CLI command that starts
    the server. This lifespan manager only handles cleanup during shutdown.
    """
    # Startup - device initialization handled by CLI
    yield
    # Shutdown - clean up device resources
    device_manager.shutdown()


# Create FastAPI application with lifespan management
app = FastAPI(
    title="BMD Signal Generator API",
    description="Real-time pattern updates for Blackmagic Design DeckLink devices",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    """
    Custom HTTP exception handler.

    Parameters
    ----------
    request
        The incoming request (unused)
    exc : HTTPException
        The HTTP exception to handle

    Returns
    -------
    JSONResponse
        Standardized error response
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=f"HTTP {exc.status_code}",
            message=exc.detail,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """
    General exception handler for unhandled errors.

    Parameters
    ----------
    request
        The incoming request (unused)
    exc : Exception
        The unhandled exception

    Returns
    -------
    JSONResponse
        Standardized error response
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            message=f"An unexpected error occurred: {exc!s}",
        ).model_dump(),
    )


@app.post(
    "/update_color",
    response_model=ColorUpdateResponse,
    summary="Update pattern colors",
    description="Update the currently displayed pattern with new colors (1-4 colors supported)",
)
async def update_color(request: ColorUpdateRequest) -> ColorUpdateResponse:
    """
    Update pattern colors without interrupting device output.

    Accepts 1-4 RGB color values and updates the currently displayed
    checkerboard pattern. Color values are validated against the device's
    current bit depth before being applied.

    Parameters
    ----------
    request : ColorUpdateRequest
        Color update request containing RGB values

    Returns
    -------
    ColorUpdateResponse
        Update result with success status and applied colors

    Raises
    ------
    HTTPException
        400: If device is not initialized
        400: If color values are invalid
        500: If pattern update fails

    Examples
    --------
    Update to white/black checkerboard:
    >>> POST /update_color
    >>> {"colors": [[4095, 4095, 4095], [0, 0, 0]]}

    Single red color:
    >>> POST /update_color
    >>> {"colors": [[4095, 0, 0]]}
    """
    if not device_manager.is_initialized():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device not initialized. Start API server via CLI first.",
        )

    try:
        result = device_manager.update_colors(request.colors)

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"],
            )

        return ColorUpdateResponse(
            success=result["success"],
            message=result["message"],
            updated_colors=result["updated_colors"],
            device_info={
                "pixel_format": (
                    device_manager._settings.pixel_format.name
                    if device_manager._settings
                    and device_manager._settings.pixel_format
                    else "Auto"
                ),
                "bit_depth": (
                    device_manager._generator.bit_depth
                    if device_manager._generator
                    else 0
                ),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update pattern: {e!s}",
        ) from e


@app.get(
    "/status",
    response_model=DeviceStatusResponse,
    summary="Get device status",
    description="Retrieve comprehensive device and pattern status information",
)
async def get_status() -> DeviceStatusResponse:
    """
    Get current device and pattern status.

    Returns comprehensive information about the connected device,
    current pattern configuration, resolution, and HDR settings.

    Returns
    -------
    DeviceStatusResponse
        Complete device and pattern status information

    Examples
    --------
    >>> GET /status
    >>> {
    ...   "device_connected": true,
    ...   "device_name": "DeckLink 8K Pro",
    ...   "pixel_format": "12-bit RGB",
    ...   "resolution": {"width": 1920, "height": 1080}
    ... }
    """
    try:
        status_info = device_manager.get_status()
        return DeviceStatusResponse(**status_info)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve device status: {e!s}",
        ) from e


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Simple health check endpoint for monitoring API server status",
)
async def health_check() -> HealthResponse:
    """
    API server health check.

    Returns basic health information including server status,
    version, and uptime. Used for monitoring and load balancer
    health checks.

    Returns
    -------
    HealthResponse
        Health status information

    Examples
    --------
    >>> GET /health
    >>> {
    ...   "status": "healthy",
    ...   "version": "0.1.0",
    ...   "uptime_seconds": 3600.0
    ... }
    """
    try:
        health_info = device_manager.get_health()
        return HealthResponse(**health_info)

    except Exception:
        # Health check should always return something
        return HealthResponse(
            status="unhealthy",
            version="0.1.0",
            uptime_seconds=0.0,
        )


@app.get(
    "/",
    summary="API root",
    description="API information and available endpoints",
)
async def root() -> dict[str, Any]:
    """
    API root endpoint with basic information.

    Returns
    -------
    Dict[str, Any]
        API information and available endpoints

    Examples
    --------
    >>> GET /
    >>> {
    ...   "name": "BMD Signal Generator API",
    ...   "version": "0.1.0",
    ...   "endpoints": ["/update_color", "/status", "/health"]
    ... }
    """
    return {
        "name": "BMD Signal Generator API",
        "version": "0.1.0",
        "description": "Real-time pattern updates for Blackmagic Design DeckLink devices",
        "endpoints": {
            "POST /update_color": "Update pattern colors (1-4 colors)",
            "GET /status": "Get device and pattern status",
            "GET /health": "Health check endpoint",
            "GET /docs": "OpenAPI documentation",
        },
        "device_initialized": device_manager.is_initialized(),
    }


__all__ = ["app"]
