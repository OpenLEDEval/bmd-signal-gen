#include "decklink_wrapper.h"
#include "pixel_packing.h"
#include <iostream>
#include <algorithm>
#include <cstring>

/*
 * Blackmagic DeckLink 12-bit RGB Interleaved Packing Implementation
 * 
 * This implementation handles the complex 12-bit RGB pixel format used by
 * Blackmagic DeckLink devices. The packing scheme is based on the DeckLink API
 * documentation and SMPTE standards for high-bit-depth video formats.
 * 
 * KEY CONCEPTS:
 * 
 * 1. PIXEL STRUCTURE:
 *    Each 12-bit RGB pixel contains:
 *    - Red channel: 12 bits (0-4095)
 *    - Green channel: 12 bits (0-4095) 
 *    - Blue channel: 12 bits (0-4095)
 *    Total: 36 bits per pixel
 * 
 * 2. CHANNEL SPLITTING:
 *    Each 12-bit channel is split into two parts:
 *    - Low 8 bits: Channel[7:0] (stored in separate bytes)
 *    - High 4 bits: Channel[11:8] (packed into combined bytes)
 * 
 * 3. INTERLEAVED PACKING:
 *    The 36 bits are distributed across 4.5 bytes per pixel:
 *    Byte 0: R_low[7:0]     (Red low 8 bits)
 *    Byte 1: G_low[7:0]     (Green low 8 bits)
 *    Byte 2: B_low[7:0]     (Blue low 8 bits)
 *    Byte 3: R_high[3:0] | G_high[3:0] << 4  (Red high 4 bits + Green high 4 bits)
 *    Byte 4: B_high[3:0] | (unused bits)     (Blue high 4 bits + padding)
 * 
 * 4. MEMORY LAYOUT:
 *    - 8 pixels fit into 36 bytes (288 bits total)
 *    - Row alignment follows DeckLink API requirements
 *    - Each row is padded to the required rowBytes alignment
 * 
 * 5. COLOR RANGE:
 *    - Input: 8-bit RGB (0-255 per channel)
 *    - Output: 12-bit RGB (0-4095 per channel)
 *    - Scaling: value_12bit = (value_8bit * 4095) / 255
 * 
 * This implementation ensures compatibility with Blackmagic hardware and
 * follows the exact packing scheme expected by the DeckLink API.
 */

// DeckLinkColorPatch Implementation
DeckLinkColorPatch::DeckLinkColorPatch() 
    : m_device(nullptr)
    , m_output(nullptr)
    , m_frame(nullptr)
    , m_width(1920)
    , m_height(1080)
    , m_r(0), m_g(0), m_b(0)
    , m_outputEnabled(false)
    , m_pixelFormat(bmdFormat8BitBGRA)
    , m_eotfType(-1)
    , m_maxCLL(0)
    , m_maxFALL(0)
    , m_formatsCached(false) {
}

DeckLinkColorPatch::~DeckLinkColorPatch() {
    closeDevice();
}

bool DeckLinkColorPatch::openDevice(int deviceIndex) {
    IDeckLinkIterator* iterator = CreateDeckLinkIteratorInstance();
    if (!iterator) return false;
    
    IDeckLink* device = nullptr;
    int current = 0;
    while (iterator->Next(&device) == S_OK) {
        if (current == deviceIndex) {
    IDeckLinkOutput* output = nullptr;
            if (device->QueryInterface(IID_IDeckLinkOutput, (void**)&output) == S_OK) {
                m_device = device;
                m_output = output;
                iterator->Release();
        return true;
            }
            device->Release();
            break;
        }
        device->Release();
        current++;
    }
    iterator->Release();
    return false;
}

void DeckLinkColorPatch::closeDevice() {
    if (m_outputEnabled) {
        stopOutput();
    }
    if (m_frame) {
        m_frame->Release();
        m_frame = nullptr;
    }
    if (m_output) {
        m_output->Release();
        m_output = nullptr;
    }
    if (m_device) {
        m_device->Release();
        m_device = nullptr;
    }
    m_formatsCached = false;
    m_supportedFormats.clear();
}

int DeckLinkColorPatch::setColor(uint16_t r, uint16_t g, uint16_t b) {
    if (!m_output) return -1;
    
    m_r = r; m_g = g; m_b = b;
    
    // Create or update frame with the selected pixel format
    if (m_frame) {
        m_frame->Release();
        m_frame = nullptr;
    }
    
    int32_t rowBytes = 0;
    HRESULT result = m_output->RowBytesForPixelFormat(m_pixelFormat, m_width, &rowBytes);
    if (result != S_OK) {
        std::cerr << "[DeckLink] RowBytesForPixelFormat failed. HRESULT: 0x" << std::hex << result << std::dec << std::endl;
        return -2;
    }
    
    std::cerr << "[DeckLink] Creating frame: " << m_width << "x" << m_height << ", format: " << getPixelFormatName(m_pixelFormat) << ", rowBytes: " << rowBytes << std::endl;
    
    result = m_output->CreateVideoFrame(m_width, m_height, rowBytes, m_pixelFormat, bmdFrameFlagDefault, &m_frame);
    if (!m_frame) {
        std::cerr << "[DeckLink] CreateVideoFrame failed. HRESULT: 0x" << std::hex << result << std::dec << std::endl;
        return -3;
    }
    
    std::cerr << "[DeckLink] Frame created successfully" << std::endl;
    
    // Fill the frame with color (handle different pixel formats)
    int fillResult = fillFrameWithColor();
    if (fillResult != 0) return fillResult;
    
    // Apply EOTF metadata if set
    if (m_eotfType >= 0) {
        int metadataResult = applyEOTFMetadata();
        if (metadataResult != 0) return metadataResult;
    }
    
    return 0;
}

void DeckLinkColorPatch::logFrameInfo(const char* context) {
    if (m_frame) {
        BMDFrameFlags flags = m_frame->GetFlags();
        int32_t width = m_frame->GetWidth();
        int32_t height = m_frame->GetHeight();
        int32_t rowBytes = m_frame->GetRowBytes();
        BMDPixelFormat format = m_frame->GetPixelFormat();
        
        std::cerr << "[DeckLink] Frame info " << context << ":" << std::endl;
        std::cerr << "  Width: " << std::dec << width << ", Height: " << std::dec << height << std::endl;
        std::cerr << "  RowBytes: " << std::dec << rowBytes << std::endl;
        std::cerr << "  PixelFormat: " << std::hex << getPixelFormatName(format) << std::dec << std::endl;
        std::cerr << "  Flags: 0x" << std::hex << flags << std::dec << std::endl;
    } else {
        std::cerr << "[DeckLink] No frame available for logging" << std::endl;
    }
}

int DeckLinkColorPatch::startOutput() {
    if (!m_output || !m_frame) return -1;
    if (m_outputEnabled) return 0;

    // Log pixel format and display mode
    std::cerr << "[DeckLink] Enabling video output: display mode bmdModeHD1080p30, pixel format: " << getPixelFormatName(m_pixelFormat) << " (" << std::hex << m_pixelFormat << ")" << std::dec << std::endl;

    HRESULT enableResult = m_output->EnableVideoOutput(bmdModeHD1080p30, bmdVideoOutputFlagDefault);
    if (enableResult != S_OK) {
        std::cerr << "[DeckLink] EnableVideoOutput failed. HRESULT: 0x" << std::hex << enableResult << std::dec << std::endl;
        return -2;
    }
    m_outputEnabled = true;

    // Log frame information before scheduling
    logFrameInfo("before scheduling");

    HRESULT schedResult = m_output->ScheduleVideoFrame(m_frame, 0, 1, 30);
    if (schedResult != S_OK) {
        std::cerr << "[DeckLink] ScheduleVideoFrame failed. HRESULT: 0x" << std::hex << schedResult << std::dec << std::endl;
        return -3;
    }
    HRESULT playResult = m_output->StartScheduledPlayback(0, 30, 1.0);
    if (playResult != S_OK) {
        std::cerr << "[DeckLink] StartScheduledPlayback failed. HRESULT: 0x" << std::hex << playResult << std::dec << std::endl;
        return -4;
    }

    return 0;
}

int DeckLinkColorPatch::stopOutput() {
    if (!m_outputEnabled) return 0;
    
    m_output->StopScheduledPlayback(0, nullptr, 0);
    m_output->DisableVideoOutput();
    m_outputEnabled = false;
    
    return 0;
}

std::vector<BMDPixelFormat> DeckLinkColorPatch::getSupportedPixelFormats() {
    if (!m_formatsCached) {
        cacheSupportedFormats();
    }
    return m_supportedFormats;
}

int DeckLinkColorPatch::setPixelFormat(int pixelFormatIndex) {
    if (!m_formatsCached) {
        cacheSupportedFormats();
    }
    
    if (pixelFormatIndex < 0 || pixelFormatIndex >= static_cast<int>(m_supportedFormats.size())) {
        return -1;
    }
    
    m_pixelFormat = m_supportedFormats[pixelFormatIndex];
    return 0;
}

int DeckLinkColorPatch::getPixelFormat() const {
    if (!m_formatsCached) {
        const_cast<DeckLinkColorPatch*>(this)->cacheSupportedFormats();
    }
    
    for (int i = 0; i < static_cast<int>(m_supportedFormats.size()); i++) {
        if (m_supportedFormats[i] == m_pixelFormat) {
            return i;
        }
    }
    return -1;
}

std::string DeckLinkColorPatch::getPixelFormatName(BMDPixelFormat format) const {
    switch (format) {
        case bmdFormat8BitYUV: return "8-bit YUV";
        case bmdFormat10BitYUV: return "10-bit YUV";
        case bmdFormat8BitARGB: return "8-bit ARGB";
        case bmdFormat8BitBGRA: return "8-bit BGRA";
        case bmdFormat10BitRGB: return "10-bit RGB";
        case bmdFormat12BitRGB: return "12-bit RGB";
        case bmdFormat12BitRGBLE: return "12-bit RGB LE";
        case bmdFormat10BitRGBXLE: return "10-bit RGBX LE";
        case bmdFormat10BitRGBX: return "10-bit RGBX";
        default: return "Unknown";
    }
}

int DeckLinkColorPatch::setEOTFMetadata(int eotf, uint16_t maxCLL, uint16_t maxFALL) {
    m_eotfType = eotf;
    m_maxCLL = maxCLL;
    m_maxFALL = maxFALL;
    return 0;
}

int DeckLinkColorPatch::getDeviceCount() {
    IDeckLinkIterator* iterator = CreateDeckLinkIteratorInstance();
    if (!iterator) return 0;
    
    int count = 0;
    IDeckLink* device = nullptr;
    while (iterator->Next(&device) == S_OK) {
        count++;
        device->Release();
    }
    iterator->Release();
    return count;
}

std::string DeckLinkColorPatch::getDeviceName(int deviceIndex) {
    IDeckLinkIterator* iterator = CreateDeckLinkIteratorInstance();
    if (!iterator) return "";
    
    IDeckLink* device = nullptr;
    int current = 0;
    while (iterator->Next(&device) == S_OK) {
        if (current == deviceIndex) {
            CFStringRef cfName = nullptr;
            std::string name = "";
            if (device->GetDisplayName(&cfName) == S_OK && cfName) {
                char nameBuf[256];
                if (CFStringGetCString(cfName, nameBuf, sizeof(nameBuf), kCFStringEncodingUTF8)) {
                    name = nameBuf;
                }
                CFRelease(cfName);
            }
            device->Release();
            iterator->Release();
            return name;
        }
        device->Release();
        current++;
    }
    iterator->Release();
    return "";
}

// Private helper methods
void DeckLinkColorPatch::cacheSupportedFormats() {
    if (!m_output) return;
    
    std::set<BMDPixelFormat> uniqueFormats;
    
    // Test common pixel formats against a standard display mode (1080p30)
    BMDPixelFormat supportedFormats[] = {
        bmdFormat8BitYUV,
        bmdFormat10BitYUV,
        bmdFormat8BitARGB,
        bmdFormat8BitBGRA,
        bmdFormat10BitRGB,
        bmdFormat12BitRGB,
        bmdFormat12BitRGBLE,
        bmdFormat10BitRGBXLE,
        bmdFormat10BitRGBX
    };
    
    for (int i = 0; i < sizeof(supportedFormats)/sizeof(supportedFormats[0]); i++) {
        BMDPixelFormat format = supportedFormats[i];
        BMDDisplayMode actualMode;
        bool supported;
        
        if (m_output->DoesSupportVideoMode(bmdVideoConnectionUnspecified, 
                                          bmdModeHD1080p30, 
                                          format, 
                                          bmdNoVideoOutputConversion, 
                                          bmdSupportedVideoModeDefault, 
                                          &actualMode, 
                                          &supported) == S_OK && supported) {
            uniqueFormats.insert(format);
        }
    }
    
    m_supportedFormats.assign(uniqueFormats.begin(), uniqueFormats.end());
    m_formatsCached = true;
}

int DeckLinkColorPatch::fillFrameWithColor() {
    if (!m_frame) return -1;
    
    IDeckLinkVideoBuffer* videoBuffer = nullptr;
    if (m_frame->QueryInterface(IID_IDeckLinkVideoBuffer, (void**)&videoBuffer) != S_OK) return -2;
    if (videoBuffer->StartAccess(bmdBufferAccessWrite) != S_OK) { videoBuffer->Release(); return -3; }
    
    void* frameData = nullptr;
    if (videoBuffer->GetBytes(&frameData) != S_OK) { 
        videoBuffer->EndAccess(bmdBufferAccessWrite); 
        videoBuffer->Release(); 
        return -4; 
    }
    
    // Get row bytes for the current pixel format
    int32_t rowBytes = 0;
    m_output->RowBytesForPixelFormat(m_pixelFormat, m_width, &rowBytes);
    
    // Use the new consistent frame-filling API
    switch (m_pixelFormat) {
        case bmdFormat8BitBGRA:
            // Scale 8-bit to 8-bit (no scaling needed, just cast)
            fill_8bit_rgb_frame(frameData, m_width, m_height, rowBytes, 
                               static_cast<uint8_t>(m_r), static_cast<uint8_t>(m_g), static_cast<uint8_t>(m_b), true);
            break;
        case bmdFormat8BitARGB:
            // Scale 8-bit to 8-bit (no scaling needed, just cast)
            fill_8bit_rgb_frame(frameData, m_width, m_height, rowBytes, 
                               static_cast<uint8_t>(m_r), static_cast<uint8_t>(m_g), static_cast<uint8_t>(m_b), false);
            break;
        case bmdFormat10BitRGB: {
            // Scale 8-bit to 10-bit before calling
            uint16_t r_10bit = (m_r * 1023) / 255;
            uint16_t g_10bit = (m_g * 1023) / 255;
            uint16_t b_10bit = (m_b * 1023) / 255;
            fill_10bit_rgb_frame(frameData, m_width, m_height, rowBytes, r_10bit, g_10bit, b_10bit);
            break;
        }
        case bmdFormat10BitYUV: {
            // Convert RGB to YUV and scale to 10-bit before calling
            uint16_t y = (66 * m_r + 129 * m_g + 25 * m_b + 128) >> 8;
            uint16_t u = (-38 * m_r - 74 * m_g + 112 * m_b + 128) >> 8;
            uint16_t v = (112 * m_r - 94 * m_g - 18 * m_b + 128) >> 8;
            y = std::max(0, std::min(1023, (int)y));
            u = std::max(0, std::min(1023, (int)(u + 512)));
            v = std::max(0, std::min(1023, (int)(v + 512)));
            fill_10bit_yuv_frame(frameData, m_width, m_height, rowBytes, y, u, v);
            break;
        }
        case bmdFormat12BitRGB: {
            // Scale 8-bit to 12-bit before calling
            uint16_t r_12bit = (m_r * 4095) / 255;
            uint16_t g_12bit = (m_g * 4095) / 255;
            uint16_t b_12bit = (m_b * 4095) / 255;
            fill_12bit_rgb_frame(frameData, m_width, m_height, rowBytes, r_12bit, g_12bit, b_12bit);
            break;
        }
        default:
            // Fallback to 8-bit BGRA for unsupported formats
            fill_8bit_rgb_frame(frameData, m_width, m_height, rowBytes, 
                               static_cast<uint8_t>(m_r), static_cast<uint8_t>(m_g), static_cast<uint8_t>(m_b), true);
            break;
    }
    
    videoBuffer->EndAccess(bmdBufferAccessWrite);
    videoBuffer->Release();
    
    return 0;
}

int DeckLinkColorPatch::applyEOTFMetadata() {
    if (!m_frame || m_eotfType < 0) return 0;
    
    // Get the metadata extensions interface
    IDeckLinkVideoFrameMutableMetadataExtensions* metadataExt = nullptr;
    HRESULT result = m_frame->QueryInterface(IID_IDeckLinkVideoFrameMutableMetadataExtensions, (void**)&metadataExt);
    if (result != S_OK || !metadataExt) return -1;
    
    // Set EOTF metadata (0-7 as per CEA 861.3)
    if (m_eotfType >= 0 && m_eotfType <= 7) {
        metadataExt->SetInt(bmdDeckLinkFrameMetadataHDRElectroOpticalTransferFunc, m_eotfType);
    }
    
    // Set HDR metadata if provided
    if (m_maxCLL > 0) {
        metadataExt->SetFloat(bmdDeckLinkFrameMetadataHDRMaximumContentLightLevel, static_cast<double>(m_maxCLL));
    }
    if (m_maxFALL > 0) {
        metadataExt->SetFloat(bmdDeckLinkFrameMetadataHDRMaximumFrameAverageLightLevel, static_cast<double>(m_maxFALL));
    }
    
    // Set the HDR metadata flag
    BMDFrameFlags currentFlags = m_frame->GetFlags();
    m_frame->SetFlags(currentFlags | bmdFrameContainsHDRMetadata);
    
    metadataExt->Release();
    return 0;
}

// Thin C wrapper implementation
extern "C" {

int decklink_get_device_count() {
    return DeckLinkColorPatch::getDeviceCount();
}

int decklink_get_device_name_by_index(int index, char* name, int name_size) {
    if (!name || name_size <= 0) return -1;
    
    std::string deviceName = DeckLinkColorPatch::getDeviceName(index);
    if (deviceName.empty()) return -1;
    
    strncpy(name, deviceName.c_str(), name_size - 1);
    name[name_size - 1] = '\0';
    return 0;
}

DeckLinkHandle decklink_open_output_by_index(int index) {
    DeckLinkColorPatch* patch = new DeckLinkColorPatch();
    if (patch->openDevice(index)) {
            return patch;
    }
    delete patch;
    return nullptr;
}

void decklink_close(DeckLinkHandle handle) {
    if (handle) {
    auto* patch = static_cast<DeckLinkColorPatch*>(handle);
    delete patch;
    }
}

int decklink_set_color(DeckLinkHandle handle, uint16_t r, uint16_t g, uint16_t b) {
    if (!handle) return -1;
    auto* patch = static_cast<DeckLinkColorPatch*>(handle);
    return patch->setColor(r, g, b);
}

int decklink_start_output(DeckLinkHandle handle) {
    if (!handle) return -1;
    auto* patch = static_cast<DeckLinkColorPatch*>(handle);
    return patch->startOutput();
}

int decklink_stop_output(DeckLinkHandle handle) {
    if (!handle) return -1;
    auto* patch = static_cast<DeckLinkColorPatch*>(handle);
    return patch->stopOutput();
}

int decklink_get_supported_pixel_format_count(DeckLinkHandle handle) {
    if (!handle) return 0;
    auto* patch = static_cast<DeckLinkColorPatch*>(handle);
    return static_cast<int>(patch->getSupportedPixelFormats().size());
}

int decklink_get_supported_pixel_format_name(DeckLinkHandle handle, int index, char* name, int name_size) {
    if (!handle || !name || name_size <= 0) return -1;
    auto* patch = static_cast<DeckLinkColorPatch*>(handle);
    
    std::vector<BMDPixelFormat> formats = patch->getSupportedPixelFormats();
    if (index < 0 || index >= static_cast<int>(formats.size())) return -1;
    
    std::string formatName = patch->getPixelFormatName(formats[index]);
    strncpy(name, formatName.c_str(), name_size - 1);
    name[name_size - 1] = '\0';
    return 0;
}

int decklink_set_pixel_format(DeckLinkHandle handle, int pixel_format_index) {
    if (!handle) return -1;
    auto* patch = static_cast<DeckLinkColorPatch*>(handle);
    return patch->setPixelFormat(pixel_format_index);
}

int decklink_get_pixel_format(DeckLinkHandle handle) {
    if (!handle) return -1;
    auto* patch = static_cast<DeckLinkColorPatch*>(handle);
    return patch->getPixelFormat();
}

int decklink_set_eotf_metadata(DeckLinkHandle handle, int eotf, uint16_t maxCLL, uint16_t maxFALL) {
    if (!handle) return -1;
    auto* patch = static_cast<DeckLinkColorPatch*>(handle);
    return patch->setEOTFMetadata(eotf, maxCLL, maxFALL);
}

} 