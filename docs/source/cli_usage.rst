CLI Usage Reference  
===================

The BMD Signal Generator command-line interface provides comprehensive control
over DeckLink devices and pattern generation.

Global Options
--------------

These options are available for all commands:

**Device Selection**
  ``--device INTEGER``
    DeckLink device index (default: 0)

**Video Configuration**  
  ``--resolution TEXT``
    Output resolution (default: "1920x1080p60")
    
  ``--pixel-format TEXT``
    Pixel format (default: auto-select, prefers 12-bit RGB)

**Region of Interest**
  ``--roi TEXT``
    Region format: "x,y,width,height" (default: full frame)

**HDR Metadata**
  ``--eotf [SDR|PQ|HLG]``
    Transfer function (default: PQ)
    
  ``--max-cll INTEGER``
    Maximum content light level in cd/m² (default: 10000)
    
  ``--max-fall INTEGER``  
    Maximum frame average light level in cd/m² (default: 400)

Commands
--------

device-details
^^^^^^^^^^^^^^^

Display information about connected DeckLink devices::

    bmd_signal_gen device-details [OPTIONS]

**Options:**
  ``--list-modes``
    Show all supported video modes for each device

**Example:**
  ``bmd_signal_gen device-details --list-modes``

checkerboard2
^^^^^^^^^^^^^

Generate a 2-color checkerboard pattern::

    bmd_signal_gen checkerboard2 [OPTIONS]

**Options:**
  ``--color1 INTEGER``
    First checkerboard color (default: 0)
    
  ``--color2 INTEGER``  
    Second checkerboard color (default: 4095)
    
  ``--duration FLOAT``
    Output duration in seconds (default: 5.0)

**Examples:**
  Basic pattern::
  
    bmd_signal_gen checkerboard2 --duration 10
    
  Custom colors::
  
    bmd_signal_gen checkerboard2 --color1 500 --color2 3500 --duration 15

checkerboard3  
^^^^^^^^^^^^^

Generate a 3-color checkerboard pattern::

    bmd_signal_gen checkerboard3 [OPTIONS]

**Options:**
  ``--color1 INTEGER``
    First color (default: 0)
    
  ``--color2 INTEGER``
    Second color (default: 2048)
    
  ``--color3 INTEGER``
    Third color (default: 4095)
    
  ``--duration FLOAT``
    Output duration in seconds (default: 5.0)

**Color Mapping:**
  3-color patterns map to a 4-color checkerboard as: [color1, color2, color3, color1]

**Example:**
  ``bmd_signal_gen checkerboard3 --color1 0 --color2 1365 --color3 2730 --duration 10``

checkerboard4
^^^^^^^^^^^^^

Generate a 4-color checkerboard pattern::

    bmd_signal_gen checkerboard4 [OPTIONS]

**Options:**
  ``--color1 INTEGER``
    Top-left color (default: 0)
    
  ``--color2 INTEGER``
    Top-right color (default: 1365)
    
  ``--color3 INTEGER``
    Bottom-left color (default: 2730)
    
  ``--color4 INTEGER``
    Bottom-right color (default: 4095)
    
  ``--duration FLOAT``
    Output duration in seconds (default: 5.0)

**Pattern Layout:**
  2x2 checkerboard with true 4-color support::
  
    +--------+--------+
    | color1 | color2 |
    +--------+--------+
    | color3 | color4 |
    +--------+--------+

**Example:**
  ``bmd_signal_gen checkerboard4 --color1 0 --color2 1000 --color3 2000 --color4 4095``

solid
^^^^^

Generate a solid color pattern::

    bmd_signal_gen solid [OPTIONS]

**Options:**
  ``--color INTEGER``
    Solid color value (default: 2048)
    
  ``--duration FLOAT``
    Output duration in seconds (default: 5.0)

**Example:**
  ``bmd_signal_gen solid --color 3000 --duration 8``

Color Values
------------

Color values depend on the pixel format bit depth:

**8-bit formats:** 0-255
**10-bit formats:** 0-1023  
**12-bit formats:** 0-4095

**Common Reference Values (12-bit):**
  * Black: 0
  * 18% Gray: 879  
  * 50% Gray: 2048
  * 75% White: 3584
  * Full White: 4095

Resolution Formats
------------------

Supported resolution strings:

**HD Formats:**
  * "1920x1080p60", "1920x1080p59.94", "1920x1080p50"
  * "1920x1080i60", "1920x1080i59.94", "1920x1080i50"
  * "1280x720p60", "1280x720p59.94", "1280x720p50"

**UHD Formats:**
  * "3840x2160p60", "3840x2160p59.94", "3840x2160p50"
  * "3840x2160p30", "3840x2160p29.97", "3840x2160p25", "3840x2160p24"

**DCI 4K:**
  * "4096x2160p60", "4096x2160p50", "4096x2160p30", "4096x2160p24"

Pixel Formats
-------------

**RGB Formats:**
  * "8bit RGB", "10bit RGB", "12bit RGB"

**YUV Formats:**
  * "8bit YUV 422", "10bit YUV 422", "10bit YUV 444"

The system auto-selects the best available format, preferring 12-bit RGB when available.

HDR Configuration
-----------------

**EOTF (Transfer Function):**
  * **SDR**: Standard Dynamic Range (Rec.709)
  * **PQ**: Perceptual Quantizer (HDR10, SMPTE ST 2084)  
  * **HLG**: Hybrid Log-Gamma (BBC/NHK HDR)

**Content Light Levels:**
  * **MaxCLL**: Peak brightness of content in cd/m²
  * **MaxFALL**: Average brightness of brightest frame in cd/m²

**Common HDR Values:**
  * Consumer HDR: MaxCLL=1000, MaxFALL=400
  * Professional HDR: MaxCLL=4000-10000, MaxFALL=400-1000
  * Cinema: MaxCLL=100-10000, varies by content

Region of Interest
------------------

The ROI parameter allows testing specific screen regions::

    --roi "x,y,width,height"

**Examples:**
  * Center 1720x880 region: ``--roi "100,100,1720,880"``
  * Upper left quadrant: ``--roi "0,0,960,540"``  
  * Custom test area: ``--roi "200,150,1520,780"``

Pattern fills the ROI area, with black borders outside the region.

Error Handling
--------------

Common error scenarios:

**Device Not Found:**
  * Verify DeckLink device connection
  * Check Desktop Video driver installation
  * Use ``device-details`` to list available devices

**Unsupported Format:**
  * Some devices don't support all pixel formats
  * Try different format or let system auto-select
  * Check device capabilities with ``device-details``

**Color Range Errors:**
  * Ensure colors are within bit-depth range  
  * 12-bit: 0-4095, 10-bit: 0-1023, 8-bit: 0-255