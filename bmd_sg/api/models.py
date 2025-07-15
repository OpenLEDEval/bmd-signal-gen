"""
Pydantic models for BMD Signal Generator API.

This module defines request and response models for the FastAPI interface,
providing type safety and automatic validation for all API endpoints.
"""

from typing import ClassVar

from pydantic import BaseModel, Field


class ColorUpdateRequest(BaseModel):
    """
    Request model for updating pattern colors.

    Accepts 1-4 RGB color values for pattern generation. Each color is
    specified as a list of 3 integers [R, G, B] representing the red,
    green, and blue channel values respectively.

    Parameters
    ----------
    colors : List[List[int]]
        List of RGB color values. Each color is a 3-element list [R, G, B].
        Valid range depends on device bit depth (0-255 for 8-bit, 0-4095 for 12-bit).

    Examples
    --------
    Single color (solid pattern):
    >>> request = ColorUpdateRequest(colors=[[4095, 0, 0]])  # Red

    Two colors (checkerboard):
    >>> request = ColorUpdateRequest(colors=[[4095, 4095, 4095], [0, 0, 0]])  # White/Black

    Four colors (full checkerboard):
    >>> request = ColorUpdateRequest(colors=[
    ...     [4095, 0, 0],     # Red
    ...     [0, 4095, 0],     # Green
    ...     [0, 0, 4095],     # Blue
    ...     [4095, 4095, 0]   # Yellow
    ... ])

    Notes
    -----
    Color validation is performed by the device manager based on the
    current pixel format's bit depth. Values outside the valid range
    will result in a validation error.
    """

    colors: list[list[int]] = Field(
        description="List of RGB color values (1-4 colors, each with 3 integers [R,G,B])",
        min_length=1,
        max_length=4,
    )

    class Config:
        json_schema_extra: ClassVar[dict] = {
            "example": {
                "colors": [
                    [4095, 4095, 4095],  # White
                    [0, 0, 0],  # Black
                ]
            }
        }


class ColorUpdateResponse(BaseModel):
    """
    Response model for color update operations.

    Provides feedback on the success of color update operations and
    returns the actual colors that were applied to the pattern.

    Parameters
    ----------
    success : bool
        Whether the color update operation succeeded
    message : str
        Human-readable status message describing the operation result
    updated_colors : List[List[int]]
        The actual RGB color values that were applied to the pattern
    device_info : dict, optional
        Additional device information (pixel format, bit depth, etc.)

    Examples
    --------
    Successful update:
    >>> response = ColorUpdateResponse(
    ...     success=True,
    ...     message="Pattern updated successfully",
    ...     updated_colors=[[4095, 4095, 4095], [0, 0, 0]]
    ... )

    Error response:
    >>> response = ColorUpdateResponse(
    ...     success=False,
    ...     message="Color value 5000 exceeds 12-bit maximum of 4095",
    ...     updated_colors=[]
    ... )
    """

    success: bool = Field(..., description="Whether the operation succeeded")
    message: str = Field(..., description="Status message describing the result")
    updated_colors: list[list[int]] = Field(
        ..., description="RGB color values that were actually applied"
    )
    device_info: dict = Field(
        default_factory=dict, description="Additional device information"
    )


class DeviceStatusResponse(BaseModel):
    """
    Response model for device status information.

    Provides comprehensive information about the current device state,
    configuration, and pattern parameters.

    Parameters
    ----------
    device_connected : bool
        Whether a DeckLink device is currently connected and active
    device_name : str
        Name of the connected DeckLink device
    pixel_format : str
        Current pixel format (e.g., "10-bit RGB", "12-bit RGB")
    resolution : dict
        Current resolution with width and height
    current_pattern : dict
        Information about the currently displayed pattern
    hdr_enabled : bool
        Whether HDR metadata is enabled
    hdr_metadata : dict, optional
        Current HDR metadata parameters

    Examples
    --------
    >>> status = DeviceStatusResponse(
    ...     device_connected=True,
    ...     device_name="DeckLink 8K Pro",
    ...     pixel_format="12-bit RGB",
    ...     resolution={"width": 1920, "height": 1080},
    ...     current_pattern={"type": "checkerboard", "colors": 2},
    ...     hdr_enabled=True
    ... )
    """

    device_connected: bool = Field(..., description="Device connection status")
    device_name: str = Field(..., description="Connected device name")
    pixel_format: str = Field(..., description="Current pixel format")
    resolution: dict = Field(..., description="Current resolution (width, height)")
    current_pattern: dict = Field(..., description="Current pattern information")
    hdr_enabled: bool = Field(..., description="HDR metadata status")
    hdr_metadata: dict = Field(
        default_factory=dict, description="HDR metadata parameters"
    )


class HealthResponse(BaseModel):
    """
    Response model for health check endpoint.

    Simple health check response indicating API server status.

    Parameters
    ----------
    status : str
        Health status ("healthy" or "unhealthy")
    version : str, optional
        API version information
    uptime_seconds : float, optional
        Server uptime in seconds

    Examples
    --------
    >>> health = HealthResponse(
    ...     status="healthy",
    ...     version="0.1.0",
    ...     uptime_seconds=3600.0
    ... )
    """

    status: str = Field(..., description="Health status")
    version: str = Field(default="0.1.0", description="API version")
    uptime_seconds: float = Field(default=0.0, description="Server uptime in seconds")


class ErrorResponse(BaseModel):
    """
    Response model for API errors.

    Standardized error response format for all API endpoints.

    Parameters
    ----------
    error : str
        Error type or category
    message : str
        Detailed error message
    details : dict, optional
        Additional error details or context

    Examples
    --------
    >>> error = ErrorResponse(
    ...     error="ValidationError",
    ...     message="Color value 5000 exceeds 12-bit maximum of 4095",
    ...     details={"invalid_color": [5000, 0, 0], "max_value": 4095}
    ... )
    """

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: dict = Field(default_factory=dict, description="Additional error details")


__all__ = [
    "ColorUpdateRequest",
    "ColorUpdateResponse",
    "DeviceStatusResponse",
    "ErrorResponse",
    "HealthResponse",
]
