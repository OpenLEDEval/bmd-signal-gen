Quick Start Guide
=================

This guide will help you get started with the BMD Signal Generator quickly.

Basic Usage
-----------

1. **Check Connected Devices**
   
   First, verify that your DeckLink device is connected and recognized::

    bmd_signal_gen device-details

   This will show all connected devices, their supported pixel formats, and HDR capabilities.

2. **Generate a Simple Test Pattern**
   
   Generate a basic 2-color checkerboard pattern::

    bmd_signal_gen checkerboard2 --device 0 --duration 10

   This creates a black and white checkerboard on device 0 for 10 seconds.

3. **Generate HDR Content**
   
   Create an HDR checkerboard with custom colors::

    bmd_signal_gen checkerboard2 --device 0 --duration 10 \
      --color1 0 --color2 2000 --eotf PQ --max-cll 4000

   This generates an HDR10 (PQ) pattern with black (0) and mid-gray (2000/4095) colors.

Common Patterns
---------------

**Two-Color Checkerboard**::

    bmd_signal_gen checkerboard2 --device 0 --duration 5 \
      --color1 100 --color2 3800

**Four-Color Checkerboard**::

    bmd_signal_gen checkerboard4 --device 0 --duration 5 \
      --color1 0 --color2 1365 --color3 2730 --color4 4095

**Solid Color**::

    bmd_signal_gen solid --device 0 --duration 5 --color 2048

Configuration Options
---------------------

**Device Selection**
  Use ``--device N`` to specify which DeckLink device to use (0, 1, 2, etc.)

**Pixel Format**
  Use ``--pixel-format`` to specify format (e.g., "10bit RGB", "12bit RGB", "10bit YUV 422")

**Resolution**
  Use ``--resolution`` to set output resolution (e.g., "1920x1080p60", "3840x2160p30")

**HDR Settings**
  * ``--eotf`` - Transfer function: SDR, PQ, HLG
  * ``--max-cll`` - Maximum content light level in cd/m²
  * ``--max-fall`` - Maximum frame average light level in cd/m²

**Region of Interest**
  Use ``--roi`` to specify a sub-region: ``--roi x,y,width,height``

Examples
--------

**Professional HDR Test Pattern**::

    bmd_signal_gen checkerboard4 --device 0 --duration 30 \
      --resolution "3840x2160p30" --pixel-format "12bit RGB" \
      --eotf PQ --max-cll 10000 --max-fall 400 \
      --color1 0 --color2 1365 --color3 2730 --color4 4095

**ROI Testing**::

    bmd_signal_gen checkerboard2 --device 0 --duration 10 \
      --roi 100,100,1720,880 --color1 0 --color2 4095

**Broadcast Safe Colors**::

    bmd_signal_gen checkerboard2 --device 0 --duration 10 \
      --color1 256 --color2 3584  # 16-235 range in 12-bit

Next Steps
----------

* See :doc:`cli_usage` for complete command reference
* See :doc:`api/bmd_sg.decklink` for programmatic usage
* See :doc:`development` for contributing to the project