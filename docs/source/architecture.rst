Architecture Overview
====================

The BMD Signal Generator is designed as a multi-layered system providing 
professional-grade video pattern generation for Blackmagic Design DeckLink devices.

System Architecture
-------------------

.. code-block:: text

    ┌─────────────────────────────────────────────────────┐
    │                 User Interfaces                     │
    ├─────────────────┬───────────────────┬───────────────┤
    │   CLI Tool      │    REST API       │  Python API   │
    │   (Typer)       │   (FastAPI)       │  (Direct)     │
    └─────────────────┴───────────────────┴───────────────┘
                                │
    ┌─────────────────────────────────────────────────────┐
    │              Python High-Level API                  │
    ├─────────────────┬───────────────────┬───────────────┤
    │  CLI Commands   │ Image Generators  │   Utilities   │
    │  (Typer Apps)   │  (NumPy Arrays)   │  (Helpers)    │
    └─────────────────┴───────────────────┴───────────────┘
                                │
    ┌─────────────────────────────────────────────────────┐
    │            DeckLink Interface Layer                 │
    ├─────────────────┬───────────────────┬───────────────┤
    │ Device Mgmt     │ Pixel Formats     │ HDR Metadata  │
    │ (RAII/adapter)  │ (Format Types)    │ (SMPTE/CEA)   │
    └─────────────────┴───────────────────┴───────────────┘
                                │
    ┌─────────────────────────────────────────────────────┐
    │            pydecklink (nanobind binding)            │
    ├─────────────────┬───────────────────┬───────────────┤
    │ DeckLink SDK    │ Pixel Packing     │ Frame Mgmt    │
    │ (Device/Frame)  │ (packing module)  │ (MutableFrame)│
    └─────────────────┴───────────────────┴───────────────┘
                                │
    ┌─────────────────────────────────────────────────────┐
    │        Blackmagic Design DeckLink SDK               │
    │              (Hardware Interface)                   │
    └─────────────────────────────────────────────────────┘

Core Components
---------------

pydecklink Device Binding
^^^^^^^^^^^^^^^^^^^^^^^^^^

**Purpose:** Low-level hardware interface and performance-critical operations.

`pydecklink <https://github.com/Fuse-Technical-Group/pydecklink>`_ binds the
DeckLink SDK with nanobind and ships prebuilt wheels. It supplies device
enumeration, synchronous and scheduled output, frame-level HDR metadata, and
byte-exact pixel packing (``pydecklink.packing``). See its SPEC.md for
binding semantics; this project documents only its own usage.

Python DeckLink Interface (``bmd_sg/decklink/``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Purpose:** High-level Python interface to DeckLink functionality.

**Key Modules:**
  * ``bmd_decklink.py`` - Protocol, adapter, and device management

**Core Classes:**
  * ``DeckLinkOutput`` - Protocol for output devices (hardware and mock)
  * ``BMDDeckLink`` - RAII adapter over ``pydecklink.Device`` with context
    manager support
  * ``HDRMetadata`` - Complete HDR metadata structure (SMPTE ST 2086, CEA-861.3)
  * ``DecklinkSettings`` - Unified configuration dataclass
  * ``PixelFormatType`` / ``EOTFType`` - Type-safe enumerations

**Design Features:**
  * Context manager protocol for safe device access
  * Device-level HDR metadata attached per frame by the adapter
  * Comprehensive type hints throughout
  * Default HDR values optimized for professional use

Pattern Generation (display-patterns)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pattern and chart generation moved to the
`display-patterns <https://github.com/OpenDisplayEval/display-patterns>`_
package (see SPEC §spec:pattern-library). ``bmd_sg.image_generators``
and ``bmd_sg.charts`` remain as deprecation shims for one release
cycle.

Command Line Interface (``bmd_sg/cli/``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Purpose:** User-friendly command-line access to all functionality.

**Architecture:**
  * ``main.py`` - Typer application with global configuration
  * ``shared.py`` - Common utilities and device management
  * ``commands/`` - Individual command implementations

**Design Patterns:**
  * Rich help panels for organized CLI options
  * Global context passing for device configuration
  * Centralized error handling and user feedback
  * Comprehensive input validation

**Command Categories:**
  * Device management (``device-details``)
  * Pattern generation (``checkerboard2/3/4``, ``solid``)
  * Future: calibration, measurement, streaming

Data Flow
---------

**Pattern Generation Flow:**

.. code-block:: text

    User Command → CLI Parsing → Device Config → Pattern Gen → Hardware Output
         │              │              │             │              │
    [Parameters]  [Validation]   [HDR Setup]   [NumPy Array]  [DeckLink SDK]
         │              │              │             │              │
    [Color Values] [Format Check] [Metadata]   [Pixel Data]   [Frame Buffer]

**Device Management Flow:**

.. code-block:: text

    Initialize → Enumerate → Configure → Start → Pattern Loop → Stop → Cleanup
         │           │          │         │           │          │        │
    [Load Lib]  [Scan HW]  [Set Format] [Begin]   [Send Frames] [End]  [RAII]

HDR Metadata Architecture
-------------------------

**Complete HDR Support:**
  * **EOTF Types:** SDR (Rec.709), PQ (HDR10), HLG (broadcast HDR)
  * **Color Primaries:** Rec.709, Rec.2020, DCI-P3, Rec.601 with precise coordinates
  * **Mastering Display:** Min/max luminance values for display capabilities
  * **Content Light Levels:** MaxCLL/MaxFALL for content brightness characteristics

**Default Configuration:**
  * MaxCLL: 10,000 cd/m² (project-specific high value for tone mapping control)
  * MaxFALL: 400 cd/m² (industry standard)
  * Primaries: Rec.2020 (Ultra HD standard)
  * EOTF: PQ (Perceptual Quantizer for HDR10)

Error Handling Strategy
-----------------------

**Layered Error Handling:**
  1. **Hardware Level** (pydecklink): SDK errors translated to exceptions
  2. **Interface Level** (Python): Device validation and format checking  
  3. **Application Level** (CLI): User-friendly error messages with context
  4. **User Level**: Clear guidance on resolution steps

**Error Categories:**
  * **Configuration Errors:** Invalid parameters, unsupported formats
  * **Hardware Errors:** Device not found, driver issues, capability mismatches
  * **Runtime Errors:** Pattern generation failures, memory issues
  * **User Errors:** Invalid color values, missing devices, permission issues

Performance Considerations
--------------------------

**Optimization Strategies:**
  * **NumPy Vectorization:** No Python loops in pattern generation
  * **Memory Layout:** Contiguous arrays for efficient hardware transfer
  * **Resource Management:** RAII patterns prevent memory leaks
  * **Format Selection:** Automatic preference for optimal pixel formats

**Benchmarks:**
  * Pattern generation: <10ms for 4K frames
  * Device initialization: <100ms typical
  * Format switching: <50ms per change
  * Memory usage: <100MB for 4K RGB 12-bit frames

Extensibility
-------------

**Plugin Architecture:**
  * Pattern generators follow common interface
  * New pixel formats added via enum extension
  * HDR metadata expandable for new standards
  * CLI commands auto-registered via module discovery

**Future Extensions:**
  * Custom pattern scripting (Python/Lua)
  * Real-time parameter control via API
  * Multi-device synchronization
  * Advanced calibration patterns
  * Network streaming capabilities

Development Principles
----------------------

**Code Quality:**
  * **DRY Principle:** Eliminate duplicate logic immediately
  * **Type Safety:** Complete type annotations throughout
  * **Documentation:** NumPy-style docstrings for all public APIs
  * **Testing:** Unit and integration tests with hardware mocking

**Architecture Goals:**
  * **Modularity:** Clear separation of concerns
  * **Maintainability:** Consistent patterns and interfaces
  * **Performance:** Optimized critical paths
  * **Reliability:** Robust error handling and resource management
  * **Usability:** Intuitive interfaces for both CLI and API use

This architecture ensures the BMD Signal Generator is both powerful for
professional use and maintainable for long-term development.