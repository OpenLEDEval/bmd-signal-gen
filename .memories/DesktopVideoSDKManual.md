# DeckLink SDK Manual - AI Agent Reference (Video-Focused)
**December 2024 - Detailed Video API Reference for AI Context**

## Contents

### Introduction
**Welcome** - BlackMagic DeckLink SDK for professional video I/O development
**Overview** - Cross-platform SDK supporting Windows, Linux, macOS for video capture, playback, and processing

### Section 1 — DeckLink SDK

#### 1.1 Scope
- **1.1.1 Supported Products** - All current DeckLink hardware including 4K Extreme, Studio, Mini series
- **1.1.2 Supported Operating Systems** - Windows 10+, Linux, macOS 10.15+
- **1.1.3 3rd Party Support** 
  - **1.1.3.1 NVIDIA GPUDirect** - Direct GPU memory access for zero-copy operations
  - **1.1.3.2 AMD DirectGMA** - AMD GPU memory access for hardware acceleration

#### 1.2 Custom Windows Installations
- **1.2.1 Supported Features** - Custom driver installations for embedded systems
- **1.2.2 Examples** - Installation scenarios for OEM integrations

#### 1.3 API Design
- **1.3.1 Object Interfaces** - COM-based interface design with consistent patterns
- **1.3.2 Reference Counting** - Memory management via AddRef/Release pattern for automatic cleanup
- **1.3.3 Interface Stability** - Version compatibility guidelines and upgrade paths
- **1.3.4 IUnknown Interface** - Base interface for all DeckLink objects
  - **1.3.4.1 IUnknown::QueryInterface** - Interface querying for capability discovery
  - **1.3.4.2 IUnknown::AddRef** - Reference counting increment for object lifetime management
  - **1.3.4.3 IUnknown::Release** - Reference counting decrement for automatic cleanup

### Section 2 — DeckLink API

#### 2.1 Using the DeckLink API in a project
Setup and initialization procedures including header files, library linking, and platform-specific considerations

#### 2.2 Sandboxing support on macOS
Security requirements and entitlements for sandboxed applications accessing hardware

#### 2.3 Accessing DeckLink devices
- **2.3.1 Windows** - COM factory instantiation using CoCreateInstance
- **2.3.2 macOS and Linux** - Platform-specific factory functions for device enumeration

#### 2.4 High level interface

##### 2.4.1 Capture
Video input workflow using IDeckLinkInput interface:
1. Enable video input with desired format and pixel format
2. Set callback to receive incoming frames
3. Start streams to begin capture
4. Process frames received via callback mechanism

##### 2.4.2 Playback
Video output workflow using IDeckLinkOutput interface:
1. Enable video output with target format
2. Create video frames using appropriate pixel format
3. Schedule frames for output with timing information
4. Start scheduled playback for synchronized output

##### 2.4.3 3D Functionality
- **2.4.3.1 3D Capture** - Dual-stream 3D video input using bmdVideoInputDualStream3D flag. Supports side-by-side, top-bottom, and frame-packed formats
- **2.4.3.2 3D Playback** - Dual-stream 3D video output using bmdVideoOutputDualStream3D flag with IDeckLinkVideoFrame3DExtensions

##### 2.4.4 DeckLink Device Notification
Device arrival/removal events via IDeckLinkDiscovery for hot-plug support:
- Install callbacks for device connection events
- Receive notifications for Thunderbolt/USB device changes
- Handle device enumeration updates dynamically

##### 2.4.5 Streaming Encoder
- **2.4.5.1 Streaming Encoder Capture** - Hardware H.264/H.265 encoding with configurable bitrates and quality settings

##### 2.4.6 Automatic Mode Detection
Format detection capabilities for incoming video signals:
- Check BMDDeckLinkSupportsInputFormatDetection capability
- Enable with bmdVideoInputEnableFormatDetection flag
- Receive format change notifications via IDeckLinkInputCallback::VideoInputFormatChanged

##### 2.4.7 Ancillary Data functionality
- **2.4.7.1 VANC Capture** - Vertical ancillary data capture including timecode, closed captions, and metadata
- **2.4.7.2 VANC Output** - Vertical ancillary data insertion for broadcast workflows

##### 2.4.8 Keying
Internal/external keying support for live production:
- Internal keying using luminance or chroma key
- External keying with separate key input
- Alpha channel support for graphics overlay

##### 2.4.9 Timecode/Timecode user bits
- **2.4.9.1 Timecode Capture** - Reading embedded VITC, LTC, and RP188 timecode
- **2.4.9.2 Timecode Output** - Embedding timecode in video output signals

##### 2.4.10 H.265 Capture
- **2.4.10.1 Encoded Capture** - Hardware H.265 encoding with HEVC profiles and levels

##### 2.4.11 Device Profiles
Multi-channel device management for cards with multiple independent channels:
- **2.4.11.1 Determine current profile ID** - Query active profile using BMDDeckLinkProfileID
- **2.4.11.2 List available profiles** - Enumerate supported configurations via IDeckLinkProfileIterator
- **2.4.11.3 Select new profile** - Switch between single/dual/quad channel modes
- **2.4.11.4 Handle profile change notification** - Respond to profile changes from other applications

##### 2.4.12 HDR Metadata
High Dynamic Range metadata support for HDR workflows:
- **2.4.12.1 CEA/SMPTE Static HDR Capture** - Capture HDR10 metadata from HDMI sources
- **2.4.12.2 CEA/SMPTE Static HDR Playback** - Output HDR10 metadata to compatible displays
- **2.4.12.3 Dolby Vision® Playback** - Dolby Vision dynamic metadata support

##### 2.4.13 Synchronized Capture/Playback
Multi-device synchronization for large installations:
- **2.4.13.1 Synchronized Capture** - Frame-accurate multi-device input using capture groups
- **2.4.13.2 Synchronized Playback** - Frame-accurate multi-device output using playback groups

##### 2.4.14 Video Frame Conversion
Format conversion utilities for real-time processing

##### 2.4.15 SMPTE 2110 IP Flows
Professional IP video transport:
- **2.4.15.1 IP Sender** - SMPTE 2110 transmission with PTP synchronization
- **2.4.15.2 IP Receiver** - SMPTE 2110 reception with automatic stream discovery

#### 2.5 Interface Reference

##### 2.5.1 IDeckLinkIterator Interface
Device enumeration entry point for discovering available hardware
- **IDeckLinkIterator::Next** - Get next available DeckLink device in system. Returns E_FAIL when no more devices available

##### 2.5.2 IDeckLink Interface  
Main device interface providing basic device information and capabilities
- **IDeckLink::GetModelName** - Returns hardware model name string (e.g., "DeckLink 4K Extreme 12G")
- **IDeckLink::GetDisplayName** - Returns user-friendly device name including index for multiple devices

##### 2.5.3 IDeckLinkOutput Interface
Comprehensive video output functionality for playback and live output

- **IDeckLinkOutput::DoesSupportVideoMode** - Tests if device supports specific display mode and pixel format combination. Returns S_OK if supported, E_FAIL if not supported

- **IDeckLinkOutput::GetDisplayMode** - Retrieves display mode information for specified mode identifier. Returns width, height, frame rate, and format flags

- **IDeckLinkOutput::IsScheduledPlaybackRunning** - Returns current playback state. S_OK indicates active playback, E_FAIL indicates stopped

- **IDeckLinkOutput::GetDisplayModeIterator** - Creates iterator for enumerating all supported display modes for device

- **IDeckLinkOutput::SetScreenPreviewCallback** - Installs callback for screen preview rendering. Supports OpenGL, DirectX, and Metal on respective platforms

- **IDeckLinkOutput::EnableVideoOutput** - Initializes video output subsystem with specified display mode and flags. Must be called before creating or scheduling frames

- **IDeckLinkOutput::DisableVideoOutput** - Shuts down video output subsystem and releases hardware resources

- **IDeckLinkOutput::CreateVideoFrame** - Allocates video frame buffer with specified dimensions and pixel format. Returns IDeckLinkMutableVideoFrame interface

- **IDeckLinkOutput::CreateVideoFrameWithBuffer** - Creates video frame using pre-allocated buffer. Useful for zero-copy operations and custom memory management

- **IDeckLinkOutput::RowBytesForPixelFormat** - Calculates stride (bytes per row) for given pixel format and width. Essential for proper buffer allocation

- **IDeckLinkOutput::CreateAncillaryData** - Creates container for VANC data insertion including timecode, closed captions, and metadata

- **IDeckLinkOutput::DisplayVideoFrameSync** - Displays frame immediately without scheduling. Blocks until frame is output. Not recommended for real-time playback

- **IDeckLinkOutput::ScheduleVideoFrame** - Queues frame for output at specified time. Core method for scheduled playback with precise timing

- **IDeckLinkOutput::SetScheduledFrameCompletionCallback** - Installs callback for frame completion notifications. Essential for continuous playback workflows

- **IDeckLinkOutput::GetBufferedVideoFrameCount** - Returns number of frames currently queued for output. Used for monitoring buffer levels

- **IDeckLinkOutput::StartScheduledPlayback** - Begins scheduled video output. Frames must be pre-queued before calling this method

- **IDeckLinkOutput::StopScheduledPlayback** - Stops scheduled video output and clears frame queue

- **IDeckLinkOutput::GetScheduledStreamTime** - Returns current stream time in specified time scale. Used for synchronization

- **IDeckLinkOutput::GetReferenceStatus** - Returns reference signal lock status for genlock applications

- **IDeckLinkOutput::GetHardwareReferenceClock** - Provides access to hardware timestamp counter for precise timing

- **IDeckLinkOutput::GetFrameCompletionReferenceTimestamp** - Returns hardware timestamp when frame was actually output

##### 2.5.4 IDeckLinkInput Interface
Comprehensive video input functionality for capture and live input

- **IDeckLinkInput::DoesSupportVideoMode** - Tests input capability for specific display mode and pixel format. Returns S_OK if input supports the combination

- **IDeckLinkInput::GetDisplayMode** - Retrieves properties of detected input signal including format, frame rate, and progressive/interlaced flags

- **IDeckLinkInput::GetDisplayModeIterator** - Creates iterator for supported input modes. Different from output modes as input depends on connected signal

- **IDeckLinkInput::SetScreenPreviewCallback** - Installs preview callback for monitoring input signal on screen

- **IDeckLinkInput::EnableVideoInput** - Initializes video input with specified format. Use bmdVideoInputEnableFormatDetection for automatic format detection

- **IDeckLinkInput::EnableVideoInputWithAllocatorProvider** - Enables input with custom memory allocator for specialized buffer management

- **IDeckLinkInput::GetAvailableVideoFrameCount** - Returns number of captured frames available for processing. Used for monitoring capture buffer levels

- **IDeckLinkInput::DisableVideoInput** - Shuts down video input and releases capture buffers

- **IDeckLinkInput::StartStreams** - Begins video capture after input is enabled and callbacks are installed

- **IDeckLinkInput::StopStreams** - Stops video capture and flushes remaining buffers

- **IDeckLinkInput::FlushStreams** - Clears capture buffers without stopping input streams

- **IDeckLinkInput::PauseStreams** - Temporarily pauses capture while maintaining buffer state

- **IDeckLinkInput::SetCallback** - Installs callback for receiving captured frames via IDeckLinkInputCallback interface

- **IDeckLinkInput::GetHardwareReferenceClock** - Provides hardware timestamp access for input timing measurements

##### 2.5.5 IDeckLinkVideoFrame Interface
Read-only access to video frame data and properties

- **IDeckLinkVideoFrame::GetWidth** - Returns frame width in pixels

- **IDeckLinkVideoFrame::GetHeight** - Returns frame height in pixels  

- **IDeckLinkVideoFrame::GetRowBytes** - Returns stride (bytes per row) including any padding required by pixel format

- **IDeckLinkVideoFrame::GetPixelFormat** - Returns BMDPixelFormat identifier for frame data layout

- **IDeckLinkVideoFrame::GetFlags** - Returns frame metadata flags including field dominance, HDR presence, and format indicators

- **IDeckLinkVideoFrame::GetTimecode** - Retrieves embedded timecode if present in frame

- **IDeckLinkVideoFrame::GetAncillaryData** - Accesses VANC data embedded in frame including closed captions and metadata

##### 2.5.6 IDeckLinkVideoOutputCallback Interface
Event notifications for video output operations
- **IDeckLinkVideoOutputCallback::ScheduledFrameCompleted** - Called when scheduled frame finishes outputting. Provides timing information and requests next frame
- **IDeckLinkVideoOutputCallback::ScheduledPlaybackHasStopped** - Notification that playback has stopped due to buffer underrun or explicit stop

##### 2.5.7 IDeckLinkMutableVideoFrame Interface
Video frame modification capabilities extending IDeckLinkVideoFrame

- **IDeckLinkMutableVideoFrame::SetFlags** - Sets frame metadata flags including field order, HDR markers, and format flags

- **IDeckLinkMutableVideoFrame::SetTimecode** - Embeds timecode in frame using BMDTimecodeFormat

- **IDeckLinkMutableVideoFrame::SetTimecodeFromComponents** - Sets timecode from individual hour/minute/second/frame components

- **IDeckLinkMutableVideoFrame::SetAncillaryData** - Embeds VANC data in frame for downstream processing

- **IDeckLinkMutableVideoFrame::SetTimecodeUserBits** - Sets 32-bit user data in timecode

- **IDeckLinkMutableVideoFrame::SetInterfaceProvider** - Associates custom interfaces with frame for extended functionality

##### 2.5.8 IDeckLinkVideoFrame3DExtensions Interface
3D video frame support for stereoscopic content
- **IDeckLinkVideoFrame3DExtensions::Get3DPackingFormat** - Returns 3D format type (side-by-side, top-bottom, frame-packed)
- **IDeckLinkVideoFrame3DExtensions::GetFrameForRightEye** - Retrieves right eye frame from 3D frame pair

##### 2.5.10 IDeckLinkInputCallback Interface
Input event notifications for capture operations
- **IDeckLinkInputCallback::VideoInputFrameArrived** - Called when new frame is captured. Provides frame data and timing information
- **IDeckLinkInputCallback::VideoInputFormatChanged** - Notification of input format change when automatic detection is enabled

##### 2.5.11 IDeckLinkVideoInputFrame Interface
Input-specific video frame properties extending IDeckLinkVideoFrame
- **IDeckLinkVideoInputFrame::GetStreamTime** - Returns capture timestamp in stream time base
- **IDeckLinkVideoInputFrame::GetHardwareReferenceTimestamp** - Returns hardware capture timestamp for precise timing

##### 2.5.13 IDeckLinkDisplayModeIterator Interface
Display mode enumeration for capability discovery
- **IDeckLinkDisplayModeIterator::Next** - Returns next supported display mode. Returns E_FAIL when enumeration complete

##### 2.5.14 IDeckLinkDisplayMode Interface
Display mode property access
- **IDeckLinkDisplayMode::GetWidth** - Returns mode width in pixels
- **IDeckLinkDisplayMode::GetHeight** - Returns mode height in pixels  
- **IDeckLinkDisplayMode::GetName** - Returns descriptive name string
- **IDeckLinkDisplayMode::GetDisplayMode** - Returns BMDDisplayMode identifier
- **IDeckLinkDisplayMode::GetFrameRate** - Returns frame rate as time value and time scale

## Extended Interfaces

### IDeckLinkConfiguration Interface
Device configuration management
- **GetInt/SetInt** - Integer configuration items (connection types, reference settings)
- **GetFloat/SetFloat** - Float configuration items (audio levels, timing adjustments)  
- **GetFlag/SetFlag** - Boolean configuration items (feature enables/disables)
- **GetString/SetString** - String configuration items (device labels, custom settings)

### IDeckLinkProfileManager Interface  
Multi-channel device profile management
- **GetProfiles** - Returns iterator for available device profiles
- **GetProfile** - Gets specific profile by BMDDeckLinkProfileID
- **SetCallback** - Installs callback for profile change notifications

### IDeckLinkVideoFrameMetadataExtensions Interface
HDR metadata access for captured frames
- **GetInt** - Integer metadata items (transfer characteristics, color primaries)
- **GetFloat** - Float metadata items (luminance values, chromaticity coordinates)
- **GetFlag** - Boolean metadata items (metadata presence flags)

### IDeckLinkVideoFrameMutableMetadataExtensions Interface
HDR metadata insertion for output frames
- **SetInt** - Set integer metadata items for HDR10 static metadata
- **SetFloat** - Set float metadata items for luminance and chromaticity
- **SetFlag** - Set boolean metadata flags

### IDeckLinkHDMIInputEDID Interface
HDMI EDID management for input devices
- **SetInt** - Configure supported features in EDID (dynamic range, color spaces)
- **SetFlag** - Enable/disable EDID features
- **WriteToEDID** - Commit EDID changes to hardware

## Key Enumerations for AI Context

### Display Modes (BMDDisplayMode)
**Standard Definition:**
- bmdModeNTSC, bmdModeNTSC2398, bmdModeNTSCp, bmdModePAL, bmdModePALp

**HD 720p:**
- bmdModeHD720p50, bmdModeHD720p5994, bmdModeHD720p60

**HD 1080:**
- bmdModeHD1080p2398, bmdModeHD1080p24, bmdModeHD1080p25
- bmdModeHD1080p2997, bmdModeHD1080p30, bmdModeHD1080p50
- bmdModeHD1080p5994, bmdModeHD1080p6000
- bmdModeHD1080i50, bmdModeHD1080i5994, bmdModeHD1080i6000

**4K UHD:**
- bmdMode4K2160p2398, bmdMode4K2160p24, bmdMode4K2160p25
- bmdMode4K2160p2997, bmdMode4K2160p30, bmdMode4K2160p50
- bmdMode4K2160p5994, bmdMode4K2160p6000

**8K UHD:**
- bmdMode8K4320p2398, bmdMode8K4320p24, bmdMode8K4320p25
- bmdMode8K4320p2997, bmdMode8K4320p30

### Pixel Formats (BMDPixelFormat)
**YUV Formats:**
- bmdFormat8BitYUV - 8-bit YUV 4:2:2 (UYVY)
- bmdFormat10BitYUV - 10-bit YUV 4:2:2 (v210)
- bmdFormat10BitYUVA - 10-bit YUV 4:2:2:4 with alpha

**RGB Formats:**
- bmdFormat8BitARGB - 8-bit ARGB 4:4:4:4
- bmdFormat8BitBGRA - 8-bit BGRA 4:4:4:4  
- bmdFormat10BitRGB - 10-bit RGB 4:4:4 (r210)
- bmdFormat12BitRGB - 12-bit RGB 4:4:4
- bmdFormat12BitRGBLE - 12-bit RGB little-endian

**Compressed Formats:**
- bmdFormatH265 - Hardware H.265/HEVC encoding
- bmdFormatDNxHR - Avid DNxHR codec support

### Video Input Flags
- **bmdVideoInputEnableFormatDetection** - Enable automatic format detection
- **bmdVideoInputDualStream3D** - Enable 3D dual-stream capture
- **bmdVideoInputSynchronizeToCaptureGroup** - Multi-device synchronization

### Video Output Flags  
- **bmdVideoOutputVANC** - Enable VANC data output
- **bmdVideoOutputVITC** - Enable VITC timecode output
- **bmdVideoOutputRP188** - Enable RP188 timecode output
- **bmdVideoOutputDualStream3D** - Enable 3D dual-stream output
- **bmdVideoOutputSynchronizeToPlaybackGroup** - Multi-device synchronization

### Frame Flags
- **bmdFrameFlagDefault** - Standard progressive frame
- **bmdFrameFlagFlipVertical** - Vertically flipped frame
- **bmdFrameContainsHDRMetadata** - Frame contains HDR metadata
- **bmdFrameContainsDolbyVisionMetadata** - Frame contains Dolby Vision metadata

### Device Capabilities (BMDDeckLinkAttribute)
- **BMDDeckLinkSupportsInputFormatDetection** - Automatic format detection support
- **BMDDeckLinkSupportsInternalKeying** - Internal keyer capability
- **BMDDeckLinkSupportsExternalKeying** - External keyer capability  
- **BMDDeckLinkSupportsHDRMetadata** - HDR metadata support
- **BMDDeckLinkSupportsDolbyVision** - Dolby Vision support
- **BMDDeckLinkSupportsDualLinkSDI** - Dual-link SDI capability
- **BMDDeckLinkSupportsQuadLinkSDI** - Quad-link SDI capability

### Configuration Items (BMDDeckLinkConfiguration)
**Video Configuration:**
- bmdDeckLinkConfigVideoOutputConnection - Output connection routing
- bmdDeckLinkConfigVideoInputConnection - Input connection routing
- bmdDeckLinkConfigHDMITimecodePacking - HDMI timecode format
- bmdDeckLinkConfigUse1080pNotPsF - Progressive vs PsF selection

**HDR Configuration:**
- bmdDeckLinkConfigHDMIInputEDIDDynamicRange - Supported HDR formats in EDID
- bmdDeckLinkConfigDolbyVisionCMVersion - Dolby Vision color management version

**Synchronization:**
- bmdDeckLinkConfigCaptureGroup - Multi-device capture synchronization group
- bmdDeckLinkConfigPlaybackGroup - Multi-device playback synchronization group

### Profile Types
- **bmdProfileOneSubDeviceFullDuplex** - Single channel full duplex
- **bmdProfileTwoSubDevicesHalfDuplex** - Dual channel half duplex  
- **bmdProfileFourSubDevices** - Quad channel operation

### 3D Packing Formats
- **bmdVideo3DPackingLeftOnly** - Left eye only
- **bmdVideo3DPackingRightOnly** - Right eye only
- **bmdVideo3DPackingSideBySideHalf** - Side-by-side half resolution
- **bmdVideo3DPackingLineByLine** - Line-by-line interleaved
- **bmdVideo3DPackingTopAndBottom** - Top-bottom stacked
- **bmdVideo3DPackingFramePacking** - Frame-packed format

## Usage Patterns for AI Agents

### Basic Device Enumeration
```cpp
// 1. Create iterator
IDeckLinkIterator* deckLinkIterator;
CoCreateInstance(CLSID_CDeckLinkIterator, NULL, CLSCTX_ALL, IID_IDeckLinkIterator, (void**)&deckLinkIterator);

// 2. Enumerate devices  
IDeckLink* deckLink;
while (deckLinkIterator->Next(&deckLink) == S_OK) {
    // Process each device
    deckLink->Release();
}
```

### Video Capture Setup
```cpp
// 1. Enable video input
deckLinkInput->EnableVideoInput(bmdModeHD1080i50, bmdFormat10BitYUV, bmdVideoInputEnableFormatDetection);

// 2. Set callback for receiving frames
deckLinkInput->SetCallback(inputCallback);

// 3. Start capture
deckLinkInput->StartStreams();

// 4. Process frames in callback
HRESULT VideoInputFrameArrived(IDeckLinkVideoInputFrame* videoFrame, IDeckLinkAudioInputPacket* audioPacket) {
    // Process video frame data
}
```

### Video Playback Setup  
```cpp
// 1. Enable video output
deckLinkOutput->EnableVideoOutput(bmdModeHD1080i50, bmdVideoOutputFlagDefault);

// 2. Create and schedule frames
IDeckLinkMutableVideoFrame* frame;
deckLinkOutput->CreateVideoFrame(1920, 1080, 3840, bmdFormat10BitYUV, bmdFrameFlagDefault, &frame);
deckLinkOutput->ScheduleVideoFrame(frame, streamTime, frameDuration, timeScale);

// 3. Start playback
deckLinkOutput->StartScheduledPlayback(0, timeScale, 1.0);
```

### HDR Metadata Handling
```cpp
// 1. Check HDR support
BMDDeckLinkAttribute attribute;
deckLinkAttributes->GetFlag(BMDDeckLinkSupportsHDRMetadata, &attribute);

// 2. Set HDR metadata on frame
IDeckLinkVideoFrameMutableMetadataExtensions* metadataExtensions;
frame->QueryInterface(IID_IDeckLinkVideoFrameMutableMetadataExtensions, (void**)&metadataExtensions);
metadataExtensions->SetInt(bmdDeckLinkFrameMetadataHDRElectroOpticalTransferFunc, 2); // PQ transfer function

// 3. Mark frame as containing HDR
frame->SetFlags(bmdFrameContainsHDRMetadata);
```

### 3D Video Processing
```cpp
// 1. Enable 3D capture
deckLinkInput->EnableVideoInput(bmdModeHD1080p24, bmdFormat10BitYUV, bmdVideoInputDualStream3D);

// 2. Access 3D frame data
IDeckLinkVideoFrame3DExtensions* threeDExtensions;
videoFrame->QueryInterface(IID_IDeckLinkVideoFrame3DExtensions, (void**)&threeDExtensions);

BMDVideo3DPackingFormat packingFormat;
threeDExtensions->Get3DPackingFormat(&packingFormat);

IDeckLinkVideoFrame* rightEyeFrame;
threeDExtensions->GetFrameForRightEye(&rightEyeFrame);
```

## Advanced Sample Functions & Patterns (From SDK 14.4 Analysis)

### Signal Generation Sample Functions

#### Core Pattern Generation Functions
Based on analysis of `SignalGenerator/` and `TestPattern/` samples:

**`FillColourBars(IDeckLinkVideoFrame& frame, bool reverse)`** - Generate SMPTE color bars
- Creates standard 75% color bars for SD/HD formats
- Supports both forward and reverse color bar patterns
- Uses predefined color arrays: `gSD75pcColourBars[8]` and `gHD75pcColourBars[8]`
- Color values pre-computed for YUV 4:2:2 format (UYVY packing)
- Essential for test pattern generation and display calibration

**`FillBlack(IDeckLinkVideoFrame& frame)`** - Generate solid black frame
- Fills entire frame buffer with video black levels
- Respects bit depth (8-bit: 16/235, 10-bit: 64/940, 12-bit: 256/3760)
- Used for blanking periods and reference black testing

**`FillSine(void* audioBuffer, uint32_t samples, uint32_t channels, uint32_t depth)`** - Generate sine wave audio
- Creates test tone at 1kHz for audio testing
- Supports multi-channel output (2, 8, 16 channels)
- Handles 16-bit and 32-bit audio sample depths
- Phase-coherent across channels for professional workflows

#### HDR Pattern Generation (From SignalGenHDR sample)

**HDR Metadata Management Functions:**

**`UpdateFrameMetadata(IDeckLinkMutableVideoFrame& frame)`** - Embed HDR metadata in frames
- Sets EOTF (PQ, HLG, SDR) transfer characteristics  
- Configures display primaries (Rec.2020, DCI-P3, Rec.709)
- Embeds mastering display luminance values (min/max)
- Sets content light levels (MaxCLL/MaxFALL)
- Marks frame with `bmdFrameContainsHDRMetadata` flag

**HDR Metadata Structure (Enhanced from samples):**
```cpp
struct HDRMetadata {
    int64_t EOTF;                          // 0=SDR, 1=Traditional HDR, 2=PQ, 3=HLG
    ChromaticityCoordinates primaries;     // Color gamut primaries and white point
    double maxDisplayMasteringLuminance;   // Peak luminance in cd/m²
    double minDisplayMasteringLuminance;   // Minimum luminance in cd/m²
    double maxCLL;                         // Maximum Content Light Level
    double maxFALL;                        // Maximum Frame Average Light Level
};
```

#### Device Management Patterns

**Device Discovery & Configuration Functions:**

**`QueryDisplayModes(DisplayModeQueryFunc callback)`** - Enumerate supported video modes
- Iterates through all supported display modes for device
- Provides callback-based access to `IDeckLinkDisplayMode` objects
- Essential for building UI mode selection menus
- Filters modes based on hardware capabilities

**`GetDeviceConfiguration()`** - Access device configuration interface
- Returns `IDeckLinkConfiguration` for hardware settings
- Supports both integer and boolean configuration items
- Examples: connection routing, reference settings, HDR capabilities
- Thread-safe configuration access patterns

**Device Callback Management (From DeckLinkOutputDevice pattern):**
- **`OnScheduledFrameCompleted(callback)`** - Frame completion notifications
- **`OnRenderAudioSamples(callback)`** - Audio buffer refill requests  
- **`OnScheduledPlaybackStopped(callback)`** - Playback halt notifications
- Uses `std::function` callbacks for modern C++ integration
- Thread-safe callback invocation with proper reference counting

### Advanced Video Output Functions

#### Frame Scheduling & Timing

**`ScheduleVideoFrame(IDeckLinkVideoFrame* frame, BMDTimeValue displayTime, BMDTimeValue duration, BMDTimeScale timeScale)`** - Enhanced usage patterns
- **Timing Calculations**: Use hardware reference clock for precise timing
- **Buffer Management**: Monitor `GetBufferedVideoFrameCount()` to prevent overflow
- **Preroll Strategy**: Schedule multiple frames before `StartScheduledPlayback()`
- **Drop Frame Handling**: Implement frame dropping for real-time applications

**Hardware Reference Clock Functions:**
- **`GetHardwareReferenceClock(BMDTimeScale, BMDTimeValue* time, BMDTimeValue* frameTime, BMDTimeValue* ticksPerFrame)`**
- **`GetFrameCompletionReferenceTimestamp(IDeckLinkVideoFrame*, BMDTimeScale, BMDTimeValue* timestamp)`**
- Critical for A/V synchronization and multi-device coordination
- Provides microsecond-accurate timing for professional workflows

#### Memory Management Patterns

**Custom Memory Allocator Integration:**
```cpp
// From SetVideoOutputFrameMemoryAllocator usage
class CustomFrameAllocator : public IDeckLinkMemoryAllocator {
    HRESULT AllocateBuffer(uint32_t bufferSize, void** allocatedBuffer);
    HRESULT ReleaseBuffer(void* buffer);
    HRESULT Commit();  // Commit allocated buffers to hardware
    HRESULT Decommit(); // Release all allocated buffers
};
```

**`CreateVideoFrameWithBuffer(width, height, rowBytes, pixelFormat, flags, buffer, IDeckLinkMutableVideoFrame**)`**
- Zero-copy frame creation using pre-allocated buffers
- Essential for GPU integration (CUDA, OpenGL, Metal)
- Enables custom memory pools for performance optimization

### Video Input Functions & Patterns

#### Automatic Format Detection

**Input Format Change Handling:**
```cpp
HRESULT VideoInputFormatChanged(BMDVideoInputFormatChangedEvents events, 
                               IDeckLinkDisplayMode* newMode, 
                               BMDDetectedVideoInputFormatFlags flags) {
    // Handle resolution, frame rate, or pixel format changes
    // Reconfigure downstream processing pipeline
    // Update UI to reflect new input format
}
```

**Format Detection Flags:**
- `bmdDetectedVideoInputYCbCr422` - YUV 4:2:2 input signal detected
- `bmdDetectedVideoInputRGB444` - RGB 4:4:4 input signal detected  
- `bmdDetectedVideoInputDualStream3D` - 3D stereoscopic input detected

#### Advanced Capture Patterns

**Multi-Device Synchronized Capture:**
- **`SetCaptureGroup(groupID)`** - Configure multi-device sync groups
- **Hardware Genlock**: Use reference input for frame-accurate synchronization
- **Buffer Coordination**: Coordinate buffer release across multiple devices
- **Timestamp Alignment**: Use `GetHardwareReferenceTimestamp()` for sync verification

### Configuration & Capability Functions

#### Device Capability Detection

**Enhanced Capability Queries:**
```cpp
// HDR capability detection
bool supportsHDR = false;
deckLinkAttributes->GetFlag(BMDDeckLinkSupportsHDRMetadata, &supportsHDR);

// 3D video support
bool supports3D = false;  
deckLinkAttributes->GetFlag(BMDDeckLinkSupportsDualStream3D, &supports3D);

// GPU acceleration support
bool supportsGPUDirect = false;
deckLinkAttributes->GetFlag(BMDDeckLinkSupportsGPUDirectCapture, &supportsGPUDirect);
```

#### Dynamic Configuration Functions

**Configuration Item Management:**
- **`SetInt(BMDDeckLinkConfigurationID, int64_t value)`** - Integer configuration
- **`SetFlag(BMDDeckLinkConfigurationID, bool value)`** - Boolean configuration  
- **`SetFloat(BMDDeckLinkConfigurationID, double value)`** - Float configuration
- **`SetString(BMDDeckLinkConfigurationID, CFStringRef value)`** - String configuration

**Real-time Configuration Examples:**
- `bmdDeckLinkConfigVideoOutputConnection` - Switch output connections
- `bmdDeckLinkConfigRec2020Output` - Force Rec.2020 color space
- `bmdDeckLinkConfigLowLatencyVideoOutput` - Enable low-latency mode
- `bmdDeckLinkConfigHDMI3DPackingFormat` - Configure 3D video packing

### Audio Functions & Integration

#### Professional Audio Patterns

**Audio Buffer Management:**
```cpp
// Continuous audio output pattern
HRESULT RenderAudioSamples(bool preroll) {
    const uint32_t kAudioWaterlevel = 48000; // Samples to maintain in buffer
    uint32_t bufferedSamples;
    GetBufferedAudioSampleFrameCount(&bufferedSamples);
    
    if (bufferedSamples < kAudioWaterlevel) {
        // Generate and schedule additional audio samples
        ScheduleAudioSamples(audioBuffer, samplesToWrite, streamTime, timeScale, &written);
    }
    return S_OK;
}
```

**Multi-Channel Audio Support:**
- **2 Channel**: Stereo output for consumer applications
- **8 Channel**: Surround sound for broadcast workflows  
- **16 Channel**: Professional multi-channel audio for large installations
- **Sample Rates**: 48kHz (broadcast), 44.1kHz (consumer), 96kHz (high-resolution)

### Error Handling & Diagnostics

#### Robust Error Management Patterns

**Frame Completion Result Handling:**
```cpp
HRESULT ScheduledFrameCompleted(IDeckLinkVideoFrame* frame, BMDOutputFrameCompletionResult result) {
    switch(result) {
        case bmdOutputFrameCompleted:
            // Frame output successfully
            break;
        case bmdOutputFrameDisplayedLate:
            // Frame displayed after deadline - monitor buffer levels
            break;
        case bmdOutputFrameDropped:
            // Frame dropped - reduce scheduling load
            break;
        case bmdOutputFrameFlushed:
            // Frame flushed during stop - clean shutdown
            break;
    }
}
```

**Reference Signal Status Monitoring:**
```cpp
BMDReferenceStatus refStatus;
deckLinkOutput->GetReferenceStatus(&refStatus);
if (refStatus & bmdReferenceNotSupportedByHardware) {
    // Hardware doesn't support reference input
} else if (refStatus & bmdReferenceLocked) {
    // Locked to external reference - genlock active
}
```

### Buffer Management & Memory Access Functions

#### Buffer Access Control Functions
**Critical for safe memory manipulation from SDK samples:**

**`IDeckLinkVideoBuffer::StartAccess(BMDBufferAccessFlags flags)`** - Begin safe buffer access
- **Parameters**: `bmdBufferAccessRead`, `bmdBufferAccessWrite`, `bmdBufferAccessReadAndWrite`
- **Usage**: Must be called before manipulating frame buffer data
- **Thread Safety**: Ensures buffer isn't modified during hardware access
- **Sample Location**: Found in SynchronizedPlayback.cpp, RP188VitcOutput.cpp

**`IDeckLinkVideoBuffer::EndAccess(BMDBufferAccessFlags flags)`** - Release buffer access lock
- **Critical**: Must match StartAccess flags and be called after buffer manipulation
- **RAII Pattern**: Use with smart pointers for automatic cleanup

**`IDeckLinkVideoBuffer::GetBytes(void** buffer)`** - Get direct pointer to buffer memory
- **Returns**: Raw pointer to video frame buffer data
- **Usage**: Call between StartAccess/EndAccess pair
- **Memory Layout**: Respects pixel format stride and padding requirements

**Safe Buffer Access Pattern:**
```cpp
// RAII buffer access helper (from ColorBars.cpp)
inline std::shared_ptr<void> ScopedBufferBytes(com_ptr<IDeckLinkMutableVideoFrame> frame, 
                                              BMDBufferAccessFlags flags = bmdBufferAccessReadAndWrite) {
    void* lockedMem;
    frame->GetBytes(&lockedMem);
    frame->StartAccess(flags);
    auto deleter = [frame, flags](void*) mutable { frame->EndAccess(flags); };
    return std::shared_ptr<void>(lockedMem, deleter);
}
```

### Precision Timing & Hardware Reference Functions

#### Hardware Reference Clock Access
**Essential for frame-accurate applications and latency measurement:**

**`IDeckLinkVideoInputFrame::GetHardwareReferenceTimestamp(BMDTimeScale timeScale, BMDTimeValue* frameTime, BMDTimeValue* frameDuration)`**
- **Purpose**: Get hardware timestamp when frame was captured
- **Precision**: Microsecond-accurate timing for A/V synchronization
- **Usage**: Critical for multi-device synchronization and latency analysis
- **Sample Location**: InputLoopThrough samples, LatencyStatistics.cpp

**`IDeckLinkOutput::GetFrameCompletionReferenceTimestamp(IDeckLinkVideoFrame* frame, BMDTimeScale timeScale, BMDTimeValue* timestamp)`**
- **Purpose**: Get hardware timestamp when frame was actually output
- **Applications**: Latency measurement, lip-sync correction, genlock verification
- **Precision**: Hardware-level timing accuracy

**ReferenceTime Utility Functions:**
```cpp
namespace ReferenceTime {
    constexpr BMDTimeScale kTimescale = 1000000;  // Microseconds
    static inline BMDTimeValue getSteadyClockUptimeCount(void);  // Cross-platform uptime
    
    // Frame timing calculations
    BMDTimeValue frameStartTime = referenceFrameTime - referenceFrameDuration;
}
```

### Multi-Device Synchronization Functions

#### Synchronized Capture/Playback Configuration
**For frame-accurate multi-device installations:**

**Device Group Configuration:**
- **`IDeckLinkConfiguration::SetInt(bmdDeckLinkConfigCaptureGroup, groupNumber)`** - Set capture sync group
- **`IDeckLinkConfiguration::SetInt(bmdDeckLinkConfigPlaybackGroup, groupNumber)`** - Set playback sync group
- **Group Numbers**: 1-4, devices in same group synchronized to hardware reference

**Synchronization Enable Flags:**
- **`bmdVideoInputSynchronizeToCaptureGroup`** - Enable input synchronization
- **`bmdVideoOutputSynchronizeToPlaybackGroup`** - Enable output synchronization
- **Hardware Requirements**: External reference signal (genlock/sync) required

**Multi-Device Setup Pattern:**
```cpp
// Configure synchronized capture group (from SynchronizedCapture.cpp)
const int32_t kSynchronizedCaptureGroup = 1;
m_deckLinkConfig->SetInt(bmdDeckLinkConfigCaptureGroup, kSynchronizedCaptureGroup);
m_deckLinkInput->EnableVideoInput(displayMode, pixelFormat, bmdVideoInputSynchronizeToCaptureGroup);
```

### Thread Management & Concurrency Patterns

#### DispatchQueue Thread Pool Implementation
**Complete thread pool for background processing (from DispatchQueue.h):**

**DispatchQueue Class Functions:**
```cpp
class DispatchQueue {
    // Thread-safe task dispatch
    template<class F, class... Args>
    void dispatch(F&& fn, Args&&... args);
    
    // Shutdown and cleanup
    void shutdown();
    
private:
    std::vector<std::thread> m_workerThreads;
    std::queue<std::function<void(void)>> m_functionQueue;
    std::condition_variable m_condition;
    std::mutex m_mutex;
    std::atomic<bool> m_shutdown;
};
```

#### Thread-Safe Sample Queues
**SampleQueue Template for A/V data buffering:**
```cpp
template<typename T>
class SampleQueue {
    void pushSample(const T& sample);      // Thread-safe enqueue
    bool popSample(T& sample);             // Non-blocking dequeue  
    bool waitForSample(T& sample);         // Blocking dequeue with timeout
    void cancelWaiters(void);              // Interrupt blocked threads for shutdown
    size_t getSize() const;                // Thread-safe size query
};
```

### Device Discovery & Notification Functions

#### Real-Time Device Monitoring
**IDeckLinkNotification Interface for hot-plug support:**

**`IDeckLinkNotification::Subscribe(BMDNotifications topic, IDeckLinkNotificationCallback* callback)`**
- **Topics**: Device arrival/removal, signal changes, hardware events
- **Callback Pattern**: Asynchronous notification delivery
- **Thread Safety**: Callbacks invoked on background thread

**`IDeckLinkNotification::Unsubscribe(BMDNotifications topic, IDeckLinkNotificationCallback* callback)`**
- **Cleanup**: Essential for proper resource management
- **Threading**: Safe to call from any thread

**Notification Callback Implementation:**
```cpp
class NotificationCallback : public IDeckLinkNotificationCallback {
    HRESULT Notify(BMDNotifications topic, uint64_t param1, uint64_t param2) override {
        switch(topic) {
            case bmdNotificationStatusChanged:
                // Handle device status changes
                break;
            case bmdNotificationDisplayModeChanged:
                // Handle input signal format changes
                break;
        }
        return S_OK;
    }
};
```

#### Device Status Monitoring
**IDeckLinkStatus Interface for hardware monitoring:**
- **Temperature Monitoring**: Device thermal status
- **Fan Speed**: Cooling system status  
- **Reference Lock**: Genlock/sync signal quality
- **Connection Status**: Cable/signal presence detection

### Advanced Video Format Functions

#### 12-Bit RGB Pixel Format Handling
**Manual pixel packing for 12-bit precision (from ColorBars.cpp):**

**12-Bit RGB Packing Pattern:**
```cpp
struct Color12BitRGB { short Red; short Green; short Blue; };

// 12-bit RGB full-range packing (8 pixels per 9 words)
void Pack12BitRGB(Color12BitRGB* colors, uint32_t* output, uint32_t pixelCount) {
    for (uint32_t i = 0; i < pixelCount; i += 8) {
        uint32_t* nextWord = &output[(i * 9) / 8];
        // Complex bit-packing algorithm for 12-bit precision
        *nextWord++ = ((colors[i].Blue & 0x0FF) << 24) | 
                      ((colors[i].Green & 0xFFF) << 12) | 
                      (colors[i].Red & 0xFFF);
        // ... continue packing remaining 7 pixels
    }
}
```

#### Dynamic Color Range Support
**EOTFColorRange handling for HDR workflows:**
```cpp
enum class EOTFColorRange { VideoRange, FullRange, PQFullRange, Size };
typedef std::array<Color12BitRGB, static_cast<size_t>(EOTFColorRange::Size)> EOTFColorArray;

// Color range conversion matrices
static const EOTFColorArray kColorBarColors = {
    // Video range, Full range, PQ full range variants
};
```

### Advanced Input Format Detection

#### Comprehensive Signal Analysis
**Enhanced format detection beyond basic capabilities:**

**`VideoInputFormatChanged` Advanced Pattern:**
```cpp
HRESULT VideoInputFormatChanged(BMDVideoInputFormatChangedEvents notificationEvents,
                               IDeckLinkDisplayMode *newMode,
                               BMDDetectedVideoInputFormatFlags detectedSignalFlags) {
    // Determine optimal pixel format based on detected signal
    BMDPixelFormat pixelFormat = (detectedSignalFlags & bmdDetectedVideoInputRGB444) ? 
                                bmdFormat10BitRGB : bmdFormat10BitYUV;
    
    // Detect 3D video signals
    bool detected3DMode = (detectedSignalFlags & bmdDetectedVideoInputDualStream3D) != 0;
    
    // Detect HDR metadata presence
    bool hasHDRMetadata = (detectedSignalFlags & bmdDetectedVideoInputHDRMetadata) != 0;
    
    // Reconfigure input pipeline for new format
    ReconfigureInputPipeline(newMode, pixelFormat, detected3DMode, hasHDRMetadata);
    return S_OK;
}
```

**Signal Quality Analysis:**
```cpp
// Input signal validation (from DeckLinkInputDevice.cpp)
bool inputFrameValid = ((videoFrame->GetFlags() & bmdFrameHasNoInputSource) == 0);
if (inputFrameValid) {
    m_seenValidSignal = true;
    AnalyzeSignalQuality(videoFrame);
}
```

### Performance Monitoring & Statistics

#### Latency Measurement System
**LatencyStatistics Class for performance analysis:**

**`LatencyStatistics` Functions:**
```cpp
class LatencyStatistics {
    void addSample(const BMDTimeValue latency);           // Add timing measurement
    BMDTimeValue getMinimum();                           // Minimum observed latency
    BMDTimeValue getMaximum();                           // Maximum observed latency
    std::pair<BMDTimeValue,BMDTimeValue> getMeanAndStdDev(); // Statistical analysis
    BMDTimeValue getRollingAverage();                    // Smoothed average
    void reset();                                        // Clear statistics
    
private:
    // Welford's algorithm for numerical stability
    uint64_t m_sampleCount;
    double m_mean, m_variance;
};
```

#### Dropped Frame Detection
**Stream continuity analysis:**
```cpp
// Stream time gap analysis for dropped frame detection
while (streamTime >= m_lastStreamTime + 2 * frameDuration) {
    m_lastStreamTime += frameDuration;
    // Report dropped frame with timestamp
    m_videoInputFrameDroppedCallback(m_lastStreamTime, frameDuration, m_frameTimescale);
}
```

### Platform-Specific Utilities

#### COM Smart Pointer Management
**Enhanced com_ptr template functions:**

**`com_ptr<T>` Advanced Functions:**
```cpp
template<typename T>
class com_ptr {
    T** releaseAndGetAddressOf();                    // For QueryInterface calls
    template<typename U>
    com_ptr(REFIID iid, com_ptr<U>& other);        // Interface conversion constructor
    template<typename U>
    com_ptr<U> queryInterface(REFIID iid) const;   // Safe interface querying
    void swap(com_ptr& other);                      // Efficient pointer swapping
};

// Factory function for interface conversion
template<typename T, typename U>
com_ptr<T> make_com_ptr(REFIID iid, com_ptr<U>& source);
```

#### Cross-Platform Timing Utilities
**Consistent timing across platforms:**
```cpp
namespace PlatformTiming {
    BMDTimeValue getHighResolutionTime();           // Platform-specific high-res timer
    void sleepForMicroseconds(BMDTimeValue usec);   // Precise sleep implementation
    BMDTimeValue convertToTimeScale(BMDTimeValue time, BMDTimeScale scale);
}
```

---
*This reference maintains detailed technical descriptions while focusing on video functionality for AI agents working with BlackMagic DeckLink SDK.*