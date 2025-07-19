# BMD Signal Generator API Documentation

FastAPI-based HTTP interface for real-time pattern updates on Blackmagic Design DeckLink devices.

## Overview

**Base URL**: `http://localhost:8000` (default)  
**Documentation**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)
**Start server**: `bmd-signal-gen api-server --device 0 --pixel-format "12-bit RGB" --resolution 1920x1080`

Server inherits all device configuration from CLI global parameters.

## Endpoints

### POST /update_color
Update pattern colors without interrupting device output.

**Request**: `{"colors": [[R,G,B], ...]}` (1-4 colors, range depends on bit depth)
**Response**: `{"success": bool, "message": str, "updated_colors": [[R,G,B], ...], "device_info": {...}}`

**Examples**:
- White/black checkerboard: `{"colors": [[4095, 4095, 4095], [0, 0, 0]]}`
- Solid red: `{"colors": [[4095, 0, 0]]}`
- Four-color checkerboard: `{"colors": [[4095,0,0], [0,4095,0], [0,0,4095], [4095,4095,0]]}`

**Errors**: 400 (invalid colors/device), 500 (update failed)

### GET /status
Get device and pattern status information.

**Response**: `{"device_connected": bool, "device_name": str, "pixel_format": str, "resolution": {"width": int, "height": int}, "current_pattern": {...}, "hdr_enabled": bool, "hdr_metadata": {...}}`

### GET /health
Health check endpoint.

**Response**: `{"status": "healthy", "version": "0.1.0", "uptime_seconds": float}`

### GET /
API root with basic information and available endpoints.

## Schema Models

**ColorUpdateRequest**: `{"colors": List[List[int]]}` (1-4 colors, each 3 integers [R,G,B])
**ColorUpdateResponse**: `{"success": bool, "message": str, "updated_colors": List[List[int]], "device_info": dict}`
**DeviceStatusResponse**: Device/pattern status with connection, format, resolution, HDR info
**HealthResponse**: `{"status": str, "version": str, "uptime_seconds": float}`
**ErrorResponse**: `{"error": str, "message": str, "details": dict}`

## Usage & Color Guidelines

**Python Client**: Use `requests` library to GET `/status` and POST `/update_color` with color data

**Bit Depth Ranges**: 8-bit (0-255), 10-bit (0-1023), 12-bit (0-4095)

**Common 12-bit Colors**: Black `[0,0,0]`, White `[4095,4095,4095]`, Conservative White `[2000,2000,2000]`, Primaries `[4095,0,0]`, `[0,4095,0]`, `[0,0,4095]`

**Pattern Expansion**: 1 color (solid), 2 colors (checkerboard), 3 colors (custom mapping), 4 colors (true 2x2)

**Error Handling**: Follow `ErrorResponse` format with error type, message, and details

**Thread Safety**: API uses thread-safe device manager for concurrent requests

**See**: `examples/api_pattern_demo.py` for complete demonstration