# Architecture Overview

This document outlines the architecture of the BMD Signal Generator application, focusing on the separation of concerns between DeckLink device setup and pattern generation/display.

## Core Concepts

### 1. DeckLink Device Setup (`DeckLinkSettings`)

This component is responsible for initializing and configuring the Blackmagic Design DeckLink device. It handles aspects such as:

*   **Device Selection:** Choosing the specific DeckLink device to use.
*   **Pixel Format:** Setting the output pixel format (e.g., 12-bit RGB, 10-bit YUV).
*   **Video Mode:** Configuring the video resolution and frame rate.
*   **HDR Metadata:** Applying global HDR metadata settings (EOTF, mastering display luminance, content light levels, chromaticity coordinates).

These settings are encapsulated in the `DeckLinkSettings` dataclass and are typically configured once when the application starts or when the device needs to be re-initialized.

### 2. Pattern Generation and Display (`PatternSettings`)

This component is responsible for generating and displaying visual patterns on the configured DeckLink device. It handles aspects such as:

*   **Pattern Type:** Specifying the type of pattern to generate (e.g., solid color, 2-color checkerboard, 4-color checkerboard).
*   **Colors:** Defining the RGB color values for the pattern.
*   **Region of Interest (ROI):** Specifying a sub-region of the frame where the pattern should be applied.

These settings are encapsulated in the `PatternSettings` dataclass. Patterns can be generated and displayed repeatedly without re-configuring the underlying DeckLink device.

## Control Flow

### Command Line Interface (CLI)

1.  **Initialization:** When the CLI application starts, it parses command-line arguments related to both DeckLink device setup and pattern generation.
2.  **DeckLink Setup:** A `DeckLinkSettings` object is created from the parsed arguments. The `setup_decklink_device` function in `bmd_sg/decklink_control.py` is called to initialize the DeckLink device with these settings.
3.  **Pattern Display:** A `PatternSettings` object is created from the parsed arguments. The `display_pattern` function in `bmd_sg/decklink_control.py` is called to generate and display the specified pattern on the already configured DeckLink device.
4.  **Cleanup:** After the pattern has been displayed for the specified duration, the `cleanup_decklink_device` function is called to stop output and close the DeckLink device.

### HTTP API

1.  **API Startup:** When the FastAPI application starts, it initializes the DeckLink device using default or pre-configured `DeckLinkSettings`.
2.  **`/bmd-signal-gen/setup` Endpoint:** This endpoint allows clients to explicitly configure the DeckLink device by providing `DeckLinkSettings`. This can be used to change resolution, HDR settings, etc., without restarting the application.
3.  **`/bmd-signal-gen/display` Endpoint:** This endpoint allows clients to display a pattern by providing `PatternSettings`. The pattern is generated and displayed on the currently configured DeckLink device. This endpoint can be called multiple times to display different patterns sequentially.
4.  **API Shutdown:** When the FastAPI application shuts down, the `cleanup_decklink_device` function is called to stop output and close the DeckLink device.

## Module Structure

*   `bmd_sg/signal_generator.py`: Defines the `DeckLinkSettings` and `PatternSettings` dataclasses.
*   `bmd_sg/decklink_control.py`: Contains core functions for DeckLink device initialization (`setup_decklink_device`) and pattern display (`display_pattern`).
*   `bmd_sg/api.py`: Implements the HTTP API endpoints for setting up the DeckLink device and displaying patterns.
*   `bmd_sg/scripts/bmd_signal_gen.py`: The main CLI entry point, responsible for parsing arguments and orchestrating the setup and display process.
*   `bmd_sg/patterns.py`: Contains the `PatternGenerator` class and `PatternType` enum for creating various visual patterns.

This separation ensures that the DeckLink device configuration is independent of the pattern being displayed, allowing for greater flexibility and reusability, especially in the context of an API that needs to display multiple patterns dynamically.