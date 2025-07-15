API Reference Guide
==================

Overview
--------

The BMD Signal Generator API provides a FastAPI-based HTTP interface for real-time pattern updates on Blackmagic Design DeckLink devices. The API maintains persistent device state and allows dynamic pattern color updates without interrupting video output.

**Key Features:**

- Real-time pattern color updates via HTTP
- Thread-safe device management for concurrent requests
- Comprehensive device status monitoring
- Integration with CLI device configuration
- Support for 1-4 color patterns with automatic expansion
- HDR metadata support with full SMPTE specifications

Getting Started
---------------

Starting the API Server
~~~~~~~~~~~~~~~~~~~~~~~~

The API server is started via the CLI command, inheriting all device configuration from global CLI parameters:

.. code-block:: bash

   # Basic server start
   bmd-signal-gen api-server

   # With device configuration
   bmd-signal-gen --device 0 --pixel-format "12-bit RGB" --resolution 1920x1080 api-server

   # With HDR configuration
   bmd-signal-gen --eotf PQ --max-cll 10000 --max-fall 400 api-server

   # Custom host and port
   bmd-signal-gen api-server --host 0.0.0.0 --port 8080

   # Development mode with auto-reload
   bmd-signal-gen api-server --reload

**Server URLs:**

- **Base URL**: ``http://localhost:8000`` (default)
- **API Documentation**: ``http://localhost:8000/docs`` (Swagger UI)
- **Alternative Docs**: ``http://localhost:8000/redoc`` (ReDoc)

Authentication
~~~~~~~~~~~~~~

No authentication is required. The API is designed for internal lab use and trusted network environments.

API Endpoints
-------------

POST /update_color
~~~~~~~~~~~~~~~~~~

Update pattern colors without interrupting device output.

**Request Schema:**

.. code-block:: json

   {
     "colors": [
       [R, G, B],
       [R, G, B],
       ...
     ]
   }

**Request Fields:**

- ``colors`` (array): List of RGB color values (1-4 colors)
- Each color is an array of 3 integers: ``[R, G, B]``
- Color value range depends on device bit depth:
  - 8-bit: 0-255
  - 10-bit: 0-1023
  - 12-bit: 0-4095

**Response Schema:**

.. code-block:: json

   {
     "success": true,
     "message": "Pattern updated successfully with 2 colors",
     "updated_colors": [
       [4095, 4095, 4095],
       [0, 0, 0]
     ],
     "device_info": {
       "pixel_format": "12-bit RGB",
       "bit_depth": 12
     }
   }

**Response Fields:**

- ``success`` (boolean): Whether the operation succeeded
- ``message`` (string): Status message describing the result
- ``updated_colors`` (array): RGB color values that were actually applied
- ``device_info`` (object): Additional device information

**Example Requests:**

White/black checkerboard (2 colors):

.. code-block:: json

   {
     "colors": [
       [4095, 4095, 4095],
       [0, 0, 0]
     ]
   }

Solid red pattern (1 color):

.. code-block:: json

   {
     "colors": [
       [4095, 0, 0]
     ]
   }

Four-color checkerboard:

.. code-block:: json

   {
     "colors": [
       [4095, 0, 0],
       [0, 4095, 0],
       [0, 0, 4095],
       [4095, 4095, 0]
     ]
   }

**Status Codes:**

- ``200``: Pattern updated successfully
- ``400``: Device not initialized or invalid color values
- ``500``: Pattern update failed

GET /status
~~~~~~~~~~~

Get comprehensive device and pattern status information.

**Response Schema:**

.. code-block:: json

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
       "color_values": [
         [4095, 4095, 4095],
         [0, 0, 0]
       ]
     },
     "hdr_enabled": true,
     "hdr_metadata": {
       "eotf": "PQ",
       "max_cll": 10000,
       "max_fall": 400,
       "primaries": "Rec.2020"
     }
   }

**Response Fields:**

- ``device_connected`` (boolean): Device connection status
- ``device_name`` (string): Connected device name
- ``pixel_format`` (string): Current pixel format
- ``resolution`` (object): Current resolution with width and height
- ``current_pattern`` (object): Current pattern information
- ``hdr_enabled`` (boolean): HDR metadata status
- ``hdr_metadata`` (object): HDR metadata parameters (if enabled)

**Status Codes:**

- ``200``: Status retrieved successfully
- ``500``: Failed to retrieve device status

GET /health
~~~~~~~~~~~

Health check endpoint for monitoring API server status.

**Response Schema:**

.. code-block:: json

   {
     "status": "healthy",
     "version": "0.1.0",
     "uptime_seconds": 3600.0
   }

**Response Fields:**

- ``status`` (string): Health status ("healthy" or "unhealthy")
- ``version`` (string): API version information
- ``uptime_seconds`` (number): Server uptime in seconds

**Status Codes:**

- ``200``: Health check successful

GET /
~~~~~

API root endpoint with basic information and available endpoints.

**Response Schema:**

.. code-block:: json

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

**Response Fields:**

- ``name`` (string): API name
- ``version`` (string): API version
- ``description`` (string): API description
- ``endpoints`` (object): Available endpoints with descriptions
- ``device_initialized`` (boolean): Whether device is initialized

**Status Codes:**

- ``200``: API information retrieved successfully

Color Value Guidelines
----------------------

Bit Depth Considerations
~~~~~~~~~~~~~~~~~~~~~~~~

Color values must be within the valid range for the current device bit depth:

- **8-bit formats**: 0-255
- **10-bit formats**: 0-1023
- **12-bit formats**: 0-4095

Common Color Values (12-bit)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Pure Black**: ``[0, 0, 0]``
- **Pure White**: ``[4095, 4095, 4095]``
- **100 nits White**: ``[2081, 2081, 2081]``
- **Conservative White**: ``[2000, 2000, 2000]`` (recommended for HDR displays)
- **Primary Red**: ``[4095, 0, 0]``
- **Primary Green**: ``[0, 4095, 0]``
- **Primary Blue**: ``[0, 0, 4095]``
- **Primary Cyan**: ``[0, 4095, 4095]``
- **Primary Magenta**: ``[4095, 0, 4095]``
- **Primary Yellow**: ``[4095, 4095, 0]``

Pattern Color Expansion
~~~~~~~~~~~~~~~~~~~~~~~

The API supports 1-4 colors with automatic pattern expansion:

- **1 color**: Solid pattern across entire frame or ROI
- **2 colors**: Standard checkerboard pattern alternating between colors
- **3 colors**: Three-color checkerboard with custom mapping
- **4 colors**: True 2x2 checkerboard with all four colors in quadrants

Error Handling
--------------

Error Response Format
~~~~~~~~~~~~~~~~~~~~~

All API errors follow a standardized format:

.. code-block:: json

   {
     "error": "ValidationError",
     "message": "Color value 5000 exceeds 12-bit maximum of 4095",
     "details": {
       "invalid_color": [5000, 0, 0],
       "max_value": 4095,
       "bit_depth": 12
     }
   }

**Error Fields:**

- ``error`` (string): Error type or category
- ``message`` (string): Detailed error message
- ``details`` (object): Additional error context

Common Error Scenarios
~~~~~~~~~~~~~~~~~~~~~~

**Device Not Initialized**

.. code-block:: json

   {
     "error": "HTTP 400",
     "message": "Device not initialized. Start API server via CLI first."
   }

**Invalid Color Values**

.. code-block:: json

   {
     "error": "HTTP 400",
     "message": "Color value 5000 exceeds 12-bit maximum of 4095"
   }

**Device Connection Error**

.. code-block:: json

   {
     "error": "HTTP 500",
     "message": "Failed to update pattern: Device connection lost"
   }

Status Codes
~~~~~~~~~~~~

- ``200``: Success - Operation completed successfully
- ``400``: Bad Request - Invalid input or device not initialized
- ``500``: Internal Server Error - Device or server failure

Usage Examples
--------------

Basic Pattern Updates
~~~~~~~~~~~~~~~~~~~~~

**Update to white/black checkerboard:**

.. code-block:: bash

   curl -X POST "http://localhost:8000/update_color" \
        -H "Content-Type: application/json" \
        -d '{
          "colors": [
            [4095, 4095, 4095],
            [0, 0, 0]
          ]
        }'

**Update to solid red:**

.. code-block:: bash

   curl -X POST "http://localhost:8000/update_color" \
        -H "Content-Type: application/json" \
        -d '{
          "colors": [
            [4095, 0, 0]
          ]
        }'

**Color bars (Cyan/Magenta/Yellow/Black):**

.. code-block:: bash

   curl -X POST "http://localhost:8000/update_color" \
        -H "Content-Type: application/json" \
        -d '{
          "colors": [
            [0, 3276, 3276],
            [3276, 0, 3276],
            [3276, 3276, 0],
            [0, 0, 0]
          ]
        }'

Device Status Monitoring
~~~~~~~~~~~~~~~~~~~~~~~~

**Check device status:**

.. code-block:: bash

   curl -X GET "http://localhost:8000/status"

**Health check:**

.. code-block:: bash

   curl -X GET "http://localhost:8000/health"

**API information:**

.. code-block:: bash

   curl -X GET "http://localhost:8000/"

Integration Guidelines
----------------------

Thread Safety
~~~~~~~~~~~~~

The API uses a thread-safe device manager singleton to handle concurrent requests safely. Multiple clients can update patterns simultaneously without device state corruption.

Performance Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Pattern updates are real-time with minimal latency
- Device state is maintained persistently to reduce initialization overhead
- NumPy-based pattern generation provides optimal performance
- No frame drops during pattern updates

External Client Implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When implementing external API clients:

1. **Start with health check** to verify server availability
2. **Check device status** to confirm device initialization
3. **Validate color values** against device bit depth before sending
4. **Handle errors gracefully** with appropriate retry logic
5. **Use appropriate timeouts** for network requests

Example Integration Flow
~~~~~~~~~~~~~~~~~~~~~~~~

1. **Server Health Check**: ``GET /health``
2. **Device Status Check**: ``GET /status``
3. **Extract bit depth** from device status for color validation
4. **Validate colors** against bit depth constraints
5. **Update pattern**: ``POST /update_color``
6. **Monitor results** via response or subsequent status checks

Best Practices
--------------

Color Value Management
~~~~~~~~~~~~~~~~~~~~~~

- Always validate color values against device bit depth
- Use conservative values for HDR displays (e.g., 2000/4095 for white)
- Test patterns with known-good color values first
- Consider gamma and color space implications

Error Handling
~~~~~~~~~~~~~~

- Implement retry logic for transient errors
- Log error details for debugging
- Provide user-friendly error messages
- Handle device disconnection gracefully

Monitoring
~~~~~~~~~~

- Use ``/health`` endpoint for automated monitoring
- Monitor ``/status`` for device state changes
- Track pattern update success rates
- Monitor server uptime and performance

Development and Testing
~~~~~~~~~~~~~~~~~~~~~~~

- Use ``--reload`` flag during development
- Test with various color combinations
- Validate against different bit depths
- Test concurrent client scenarios
- Monitor resource usage during extended operation

This API provides a robust interface for external systems to integrate with BMD Signal Generator functionality, enabling automated testing workflows and remote pattern control.