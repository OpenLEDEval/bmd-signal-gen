# BMD Signal Generator API Documentation

This document provides comprehensive documentation for the BMD Signal Generator REST API, including all endpoints, schemas, and usage examples.

## API Overview

The BMD Signal Generator API provides a FastAPI-based HTTP interface for real-time pattern updates on Blackmagic Design DeckLink devices. The API maintains device state and allows dynamic pattern color updates without interrupting video output.

**Base URL**: `http://localhost:8000` (default)  
**Documentation**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)

## Starting the API Server

The API server is started via the CLI command:

```bash
bmd-signal-gen api-server --device 0 --pixel-format "12-bit RGB" --resolution 1920x1080
```

The server inherits all device configuration from the CLI global parameters (device index, pixel format, resolution, HDR settings, etc.).

## Endpoints

### POST /update_color

Update pattern colors without interrupting device output.

**Request Schema**: `ColorUpdateRequest`
- `colors`: List of RGB color values (1-4 colors, each with 3 integers [R,G,B])
- Valid color range depends on device bit depth (0-255 for 8-bit, 0-4095 for 12-bit)

**Response Schema**: `ColorUpdateResponse`
- `success`: Whether the operation succeeded
- `message`: Status message describing the result
- `updated_colors`: RGB color values that were actually applied
- `device_info`: Additional device information (pixel format, bit depth)

**Examples**:

White/black checkerboard (2 colors):
```json
POST /update_color
{
  "colors": [
    [4095, 4095, 4095],
    [0, 0, 0]
  ]
}
```

Solid red pattern (1 color):
```json
POST /update_color
{
  "colors": [
    [4095, 0, 0]
  ]
}
```

Four-color checkerboard:
```json
POST /update_color
{
  "colors": [
    [4095, 0, 0],     # Red
    [0, 4095, 0],     # Green  
    [0, 0, 4095],     # Blue
    [4095, 4095, 0]   # Yellow
  ]
}
```

**Error Responses**:
- `400`: Device not initialized or invalid color values
- `500`: Pattern update failed

### GET /status

Get comprehensive device and pattern status information.

**Response Schema**: `DeviceStatusResponse`
- `device_connected`: Whether a DeckLink device is connected and active
- `device_name`: Name of the connected DeckLink device
- `pixel_format`: Current pixel format (e.g., "12-bit RGB", "10-bit YUV")
- `resolution`: Current resolution with width and height
- `current_pattern`: Information about the currently displayed pattern
- `hdr_enabled`: Whether HDR metadata is enabled
- `hdr_metadata`: Current HDR metadata parameters (if enabled)

**Example Response**:
```json
{
  "device_connected": true,
  "device_name": "DeckLink 8K Pro",
  "pixel_format": "12-bit RGB",
  "resolution": {
    "width": 1920,
    "height": 1080
  },
  "current_pattern": {
    "type": "checkerboard",
    "colors": 2,
    "roi": {
      "x": 100,
      "y": 100,
      "width": 1720,
      "height": 880
    }
  },
  "hdr_enabled": true,
  "hdr_metadata": {
    "eotf": "PQ",
    "max_cll": 10000,
    "max_fall": 400,
    "primaries": "Rec.2020"
  }
}
```

### GET /health

Health check endpoint for monitoring API server status.

**Response Schema**: `HealthResponse`
- `status`: Health status ("healthy" or "unhealthy")
- `version`: API version information
- `uptime_seconds`: Server uptime in seconds

**Example Response**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 3600.0
}
```

### GET /

API root endpoint with basic information and available endpoints.

**Example Response**:
```json
{
  "name": "BMD Signal Generator API",
  "version": "0.1.0",
  "description": "Real-time pattern updates for Blackmagic Design DeckLink devices",
  "endpoints": {
    "POST /update_color": "Update pattern colors (1-4 colors)",
    "GET /status": "Get device and pattern status",
    "GET /health": "Health check endpoint",
    "GET /docs": "OpenAPI documentation"
  },
  "device_initialized": true
}
```

## Schema Models

### ColorUpdateRequest

Request model for updating pattern colors.

**Fields**:
- `colors`: `List[List[int]]` - List of RGB color values (1-4 colors, each with 3 integers [R,G,B])

**Validation**:
- Minimum 1 color, maximum 4 colors
- Each color must be exactly 3 integers [R, G, B]
- Color values validated against device bit depth at runtime

### ColorUpdateResponse

Response model for color update operations.

**Fields**:
- `success`: `bool` - Whether the operation succeeded
- `message`: `str` - Status message describing the result
- `updated_colors`: `List[List[int]]` - RGB color values that were actually applied
- `device_info`: `dict` - Additional device information (pixel format, bit depth)

### DeviceStatusResponse

Response model for device status information.

**Fields**:
- `device_connected`: `bool` - Device connection status
- `device_name`: `str` - Connected device name
- `pixel_format`: `str` - Current pixel format
- `resolution`: `dict` - Current resolution (width, height)
- `current_pattern`: `dict` - Current pattern information
- `hdr_enabled`: `bool` - HDR metadata status
- `hdr_metadata`: `dict` - HDR metadata parameters

### HealthResponse

Response model for health check endpoint.

**Fields**:
- `status`: `str` - Health status ("healthy" or "unhealthy")
- `version`: `str` - API version (default: "0.1.0")
- `uptime_seconds`: `float` - Server uptime in seconds

### ErrorResponse

Standardized error response format for all API endpoints.

**Fields**:
- `error`: `str` - Error type or category
- `message`: `str` - Detailed error message
- `details`: `dict` - Additional error details or context

## Usage Examples

### Python Client Example

```python
import requests

# Check server status
response = requests.get("http://localhost:8000/status")
status = response.json()
print(f"Device: {status['device_name']}")

# Update to white/black checkerboard
colors = {
    "colors": [
        [4095, 4095, 4095],  # White
        [0, 0, 0]            # Black
    ]
}
response = requests.post("http://localhost:8000/update_color", json=colors)
result = response.json()
print(f"Update result: {result['message']}")
```

### Complete Demo

See `examples/api_pattern_demo.py` for a complete demonstration showing:
- API server connectivity check
- Multiple pattern updates in sequence
- Error handling and status monitoring
- Practical color values for different patterns

## Color Value Guidelines

### Bit Depth Considerations

- **8-bit formats**: Color values 0-255
- **10-bit formats**: Color values 0-1023  
- **12-bit formats**: Color values 0-4095

### Common Color Values (12-bit)

- **Pure Black**: `[0, 0, 0]`
- **Pure White**: `[4095, 4095, 4095]`
- **100 nits White**: `[2081, 2081, 2081]`
- **Conservative White**: `[2000, 2000, 2000]` (recommended for HDR displays)
- **Primary Red**: `[4095, 0, 0]`
- **Primary Green**: `[0, 4095, 0]`
- **Primary Blue**: `[0, 0, 4095]`

### Pattern Color Expansion

The API supports 1-4 colors with automatic expansion:
- **1 color**: Solid pattern across entire frame/ROI
- **2 colors**: Standard checkerboard pattern
- **3 colors**: Three-color checkerboard with custom mapping
- **4 colors**: True 2x2 checkerboard with all four colors

## Error Handling

### Common Error Scenarios

1. **Device Not Initialized**: Start API server via CLI first
2. **Invalid Color Values**: Color values exceed bit depth maximum
3. **Network Errors**: API server not running or unreachable
4. **Device Disconnected**: DeckLink device hardware issue

### Error Response Format

All errors follow the standardized `ErrorResponse` format:

```json
{
  "error": "ValidationError",
  "message": "Color value 5000 exceeds 12-bit maximum of 4095",
  "details": {
    "invalid_color": [5000, 0, 0],
    "max_value": 4095,
    "bit_depth": 12
  }
}
```

## Thread Safety

The API uses a thread-safe device manager singleton to handle concurrent requests safely. Multiple clients can update patterns simultaneously without device state corruption.

## Memory File Maintenance

**Important**: When making significant changes to the API structure, endpoints, or schemas, please update the project memory file at `.memories/PROJECT_SUMMARY.md`. This helps maintain accurate context for future development.

**Update the memory file when**:
- Adding new endpoints or removing existing ones
- Changing request/response schemas significantly
- Modifying core API behavior or configuration
- Adding new features that change the API surface

The memory file should reflect the current state of the API to ensure accurate assistance for future development work.