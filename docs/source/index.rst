BMD Signal Generator Documentation
===================================

.. warning::
   **AI-Generated Documentation Notice**
   
   Much of this project's documentation was generated using AI assistance. The project and its documentation may contain bugs, missing features, or may not work correctly on certain hardware or operating system configurations. The authors primarily develop on macOS but have made their best effort to make the software cross-platform. If you encounter issues or have questions, please start a `GitHub Discussion <https://github.com/YOUR_ORG/bmd-signal-gen/discussions>`_.

Cross-platform BMD signal generator for Blackmagic Design DeckLink devices with HDR metadata support.

The BMD Signal Generator is a comprehensive tool for generating test patterns via professional video hardware.
It consists of a C++ core for low-level DeckLink SDK integration, a Python library with high-level interfaces,
a command-line tool, and a REST API for pattern generation.

Features
--------

* **HDR Support**: Complete HDR metadata with SMPTE ST 2086 and CEA-861.3 standards
* **Multiple Formats**: 8-bit to 12-bit support with YUV/RGB variants  
* **Test Patterns**: Checkerboard patterns, solid colors, and more
* **Cross-Platform**: Windows, macOS, and Linux support
* **Professional Grade**: Built for broadcast and video production workflows

Quick Start
-----------

Install the package and generate a test pattern::

    pip install bmd-signal-generator
    bmd_signal_gen checkerboard2 --device 0 --duration 10

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Guide:

   installation
   quickstart
   cli_usage
   api_guide

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   api/bmd_sg.decklink
   api/bmd_sg.image_generators  
   api/bmd_sg.cli
   api/bmd_sg.utilities

.. toctree::
   :maxdepth: 2
   :caption: Developer Guide:

   development
   architecture

