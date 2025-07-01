#include "decklink_wrapper.h"
#include "pixel_packing.h"
#include "draw_image.h"
#include <iostream>
#include <algorithm>
#include <cstring>
#include "DeckLinkAPIVersion.h"
#include <CoreFoundation/CoreFoundation.h>

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

// DeckLinkSignalGen Implementation
DeckLinkSignalGen::DeckLinkSignalGen() 
    : m_device(nullptr)
    , m_output(nullptr)
    , m_frame(nullptr)
    , m_width(1920)
    , m_height(1080)

    , m_outputEnabled(false)
    , m_pixelFormat(bmdFormat8BitBGRA)
    , m_eotfType(-1)
    , m_maxCLL(0)
    , m_maxFALL(0)
    , m_formatsCached(false) {
}

DeckLinkSignalGen::~DeckLinkSignalGen() {
    closeDevice();
}

bool DeckLinkSignalGen::openDevice(int deviceIndex) {
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

void DeckLinkSignalGen::closeDevice() {
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



void DeckLinkSignalGen::logFrameInfo(const char* context) {
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

int DeckLinkSignalGen::startOutput() {
    if (!m_output) return -1;
    if (m_outputEnabled) return 0;

    // Log pixel format and display mode
    std::cerr << "[DeckLink] Enabling video output: display mode bmdModeHD1080p30, pixel format: " << getPixelFormatName(m_pixelFormat) << " (" << std::hex << m_pixelFormat << ")" << std::dec << std::endl;

    HRESULT enableResult = m_output->EnableVideoOutput(bmdModeHD1080p30, bmdVideoOutputFlagDefault);
    if (enableResult != S_OK) {
        std::cerr << "[DeckLink] EnableVideoOutput failed. HRESULT: 0x" << std::hex << enableResult << std::dec << std::endl;
        return -2;
    }
    m_outputEnabled = true;

    // Create frame from pending data if available
    if (!m_frame && !m_pendingFrameData.empty()) {
        int32_t rowBytes = 0;
        HRESULT result = m_output->RowBytesForPixelFormat(m_pixelFormat, m_width, &rowBytes);
        if (result != S_OK) {
            std::cerr << "[DeckLink] RowBytesForPixelFormat failed. HRESULT: 0x" << std::hex << result << std::dec << std::endl;
            return -3;
        }
        
        result = m_output->CreateVideoFrame(m_width, m_height, rowBytes, m_pixelFormat, bmdFrameFlagDefault, &m_frame);
        if (!m_frame) {
            std::cerr << "[DeckLink] CreateVideoFrame failed. HRESULT: 0x" << std::hex << result << std::dec << std::endl;
            return -4;
        }
        
        // Copy pending data to frame
        IDeckLinkVideoBuffer* videoBuffer = nullptr;
        if (m_frame->QueryInterface(IID_IDeckLinkVideoBuffer, (void**)&videoBuffer) != S_OK) return -5;
        if (videoBuffer->StartAccess(bmdBufferAccessWrite) != S_OK) { videoBuffer->Release(); return -6; }
        
        void* frameData = nullptr;
        if (videoBuffer->GetBytes(&frameData) != S_OK) { 
            videoBuffer->EndAccess(bmdBufferAccessWrite); 
            videoBuffer->Release(); 
            return -7; 
        }
        
        // Use pixel packing system to convert raw RGB data to the target format
        const uint8_t* srcData = m_pendingFrameData.data();
        
        // Extract RGB channels from the raw data (3 bytes per pixel: R, G, B)
        std::vector<uint8_t> r_channel(m_width * m_height);
        std::vector<uint8_t> g_channel(m_width * m_height);
        std::vector<uint8_t> b_channel(m_width * m_height);
        
        for (int i = 0; i < m_width * m_height; i++) {
            r_channel[i] = srcData[i * 3 + 0];
            g_channel[i] = srcData[i * 3 + 1];
            b_channel[i] = srcData[i * 3 + 2];
        }
        
        // Pack the data according to the pixel format
        switch (m_pixelFormat) {
            case bmdFormat8BitBGRA:
                pack_8bit_rgb_image(frameData, r_channel.data(), g_channel.data(), b_channel.data(),
                                  m_width, m_height, rowBytes, true);
                break;
            case bmdFormat8BitARGB:
                pack_8bit_rgb_image(frameData, r_channel.data(), g_channel.data(), b_channel.data(),
                                  m_width, m_height, rowBytes, false);
                break;
            case bmdFormat10BitRGB: {
                // Convert 8-bit to 10-bit
                std::vector<uint16_t> r_10bit(m_width * m_height);
                std::vector<uint16_t> g_10bit(m_width * m_height);
                std::vector<uint16_t> b_10bit(m_width * m_height);
                
                for (int i = 0; i < m_width * m_height; i++) {
                    r_10bit[i] = (r_channel[i] * 1023) / 255;
                    g_10bit[i] = (g_channel[i] * 1023) / 255;
                    b_10bit[i] = (b_channel[i] * 1023) / 255;
                }
                
                pack_10bit_rgb_image(frameData, r_10bit.data(), g_10bit.data(), b_10bit.data(),
                                   m_width, m_height, rowBytes);
                break;
            }
            case bmdFormat10BitYUV: {
                // Convert RGB to YUV and scale to 10-bit
                std::vector<uint16_t> y_channel(m_width * m_height);
                std::vector<uint16_t> u_channel(m_width * m_height);
                std::vector<uint16_t> v_channel(m_width * m_height);
                
                for (int i = 0; i < m_width * m_height; i++) {
                    uint16_t r = r_channel[i];
                    uint16_t g = g_channel[i];
                    uint16_t b = b_channel[i];
                    
                    // RGB to YUV conversion
                    y_channel[i] = (66 * r + 129 * g + 25 * b + 128) >> 8;
                    u_channel[i] = ((-38 * r - 74 * g + 112 * b + 128) >> 8) + 512;
                    v_channel[i] = ((112 * r - 94 * g - 18 * b + 128) >> 8) + 512;
                    
                    // Clamp to 10-bit range
                    y_channel[i] = std::max(0, std::min(1023, (int)y_channel[i]));
                    u_channel[i] = std::max(0, std::min(1023, (int)u_channel[i]));
                    v_channel[i] = std::max(0, std::min(1023, (int)v_channel[i]));
                }
                
                pack_10bit_yuv_image(frameData, y_channel.data(), u_channel.data(), v_channel.data(),
                                   m_width, m_height, rowBytes);
                break;
            }
            case bmdFormat12BitRGB: {
                // Convert 8-bit to 12-bit
                std::vector<uint16_t> r_12bit(m_width * m_height);
                std::vector<uint16_t> g_12bit(m_width * m_height);
                std::vector<uint16_t> b_12bit(m_width * m_height);
                
                for (int i = 0; i < m_width * m_height; i++) {
                    r_12bit[i] = (r_channel[i] * 4095) / 255;
                    g_12bit[i] = (g_channel[i] * 4095) / 255;
                    b_12bit[i] = (b_channel[i] * 4095) / 255;
                }
                
                pack_12bit_rgb_image(frameData, r_12bit.data(), g_12bit.data(), b_12bit.data(),
                                   m_width, m_height, rowBytes);
                break;
            }
            default:
                std::cerr << "[DeckLink] Unsupported pixel format for packing: " << getPixelFormatName(m_pixelFormat) << std::endl;
                // Fallback to simple copy (may not work correctly)
                memcpy(frameData, m_pendingFrameData.data(), rowBytes * m_height);
                break;
        }
        
        videoBuffer->EndAccess(bmdBufferAccessWrite);
        videoBuffer->Release();
        
        // Apply EOTF metadata if set
        if (m_eotfType >= 0) {
            int metadataResult = applyEOTFMetadata();
            if (metadataResult != 0) return metadataResult;
        }
    }

    if (!m_frame) {
        std::cerr << "[DeckLink] No frame available for output" << std::endl;
        return -8;
    }

    // Log frame information before scheduling
    logFrameInfo("before scheduling");

    HRESULT schedResult = m_output->ScheduleVideoFrame(m_frame, 0, 1, 30);
    if (schedResult != S_OK) {
        std::cerr << "[DeckLink] ScheduleVideoFrame failed. HRESULT: 0x" << std::hex << schedResult << std::dec << std::endl;
        return -9;
    }
    HRESULT playResult = m_output->StartScheduledPlayback(0, 30, 1.0);
    if (playResult != S_OK) {
        std::cerr << "[DeckLink] StartScheduledPlayback failed. HRESULT: 0x" << std::hex << playResult << std::dec << std::endl;
        return -10;
    }

    return 0;
}

int DeckLinkSignalGen::stopOutput() {
    if (!m_outputEnabled) return 0;
    
    m_output->StopScheduledPlayback(0, nullptr, 0);
    m_output->DisableVideoOutput();
    m_outputEnabled = false;
    
    return 0;
}

std::vector<BMDPixelFormat> DeckLinkSignalGen::getSupportedPixelFormats() {
    if (!m_formatsCached) {
        cacheSupportedFormats();
    }
    return m_supportedFormats;
}

int DeckLinkSignalGen::setPixelFormat(int pixelFormatIndex) {
    if (!m_formatsCached) {
        cacheSupportedFormats();
    }
    
    if (pixelFormatIndex < 0 || pixelFormatIndex >= static_cast<int>(m_supportedFormats.size())) {
        std::cerr << "[DeckLink] Invalid pixel format index: " << pixelFormatIndex << " (valid range: 0-" << m_supportedFormats.size()-1 << ")" << std::endl;
        return -1;
    }
    
    m_pixelFormat = m_supportedFormats[pixelFormatIndex];
    return 0;
}

int DeckLinkSignalGen::getPixelFormat() const {
    if (!m_formatsCached) {
        const_cast<DeckLinkSignalGen*>(this)->cacheSupportedFormats();
    }
    
    for (int i = 0; i < static_cast<int>(m_supportedFormats.size()); i++) {
        if (m_supportedFormats[i] == m_pixelFormat) {
            return i;
        }
    }
    return -1;
}

std::string DeckLinkSignalGen::getPixelFormatName(BMDPixelFormat format) const {
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

int DeckLinkSignalGen::setEOTFMetadata(int eotf, uint16_t maxCLL, uint16_t maxFALL) {
    m_eotfType = eotf;
    m_maxCLL = maxCLL;
    m_maxFALL = maxFALL;
    return 0;
}

int DeckLinkSignalGen::setFrameData(const uint8_t* data, int width, int height, BMDPixelFormat pixel_format) {
    if (!m_output || !data) return -1;
    
    // Handle pixel format parameter - it can be either an index or a BMDPixelFormat value
    BMDPixelFormat targetFormat = m_pixelFormat; // Default to current format
    
    if (pixel_format >= 0) {
        // Check if this looks like an index (small positive number)
        if (pixel_format < 100) {
            // Treat as index into supported formats
            if (!m_formatsCached) {
                cacheSupportedFormats();
            }
            
            if (pixel_format >= 0 && pixel_format < static_cast<int>(m_supportedFormats.size())) {
                targetFormat = m_supportedFormats[pixel_format];
            } else {
                std::cerr << "[DeckLink] setFrameData: Invalid pixel format index " << pixel_format 
                          << " (valid range: 0-" << m_supportedFormats.size()-1 << "), using current format" << std::endl;
            }
        } else {
            // Treat as direct BMDPixelFormat value
            targetFormat = pixel_format;
        }
    }
    
    // Update dimensions and pixel format if needed
    if (width != m_width || height != m_height || targetFormat != m_pixelFormat) {
        m_width = width;
        m_height = height;
        m_pixelFormat = targetFormat;
        
        // Create new frame with new parameters
        if (m_frame) {
            m_frame->Release();
            m_frame = nullptr;
        }
    }
    
    // Store the raw RGB data (3 bytes per pixel: R, G, B)
    m_pendingFrameData = std::vector<uint8_t>(data, data + (width * height * 3));
    
    return 0;
}

uint8_t* DeckLinkSignalGen::getFrameBuffer(int* width, int* height, int* row_bytes) {
    if (!m_output || !width || !height || !row_bytes) return nullptr;
    
    // Create frame if it doesn't exist
    if (!m_frame) {
        // Enable video output if not already enabled
        if (!m_outputEnabled) {
            HRESULT enableResult = m_output->EnableVideoOutput(bmdModeHD1080p30, bmdVideoOutputFlagDefault);
            if (enableResult != S_OK) return nullptr;
            m_outputEnabled = true;
        }
        
        int32_t rowBytes = 0;
        HRESULT result = m_output->RowBytesForPixelFormat(m_pixelFormat, m_width, &rowBytes);
        if (result != S_OK) return nullptr;
        
        result = m_output->CreateVideoFrame(m_width, m_height, rowBytes, m_pixelFormat, bmdFrameFlagDefault, &m_frame);
        if (!m_frame) return nullptr;
    }
    
    // Get frame buffer
    IDeckLinkVideoBuffer* videoBuffer = nullptr;
    if (m_frame->QueryInterface(IID_IDeckLinkVideoBuffer, (void**)&videoBuffer) != S_OK) return nullptr;
    if (videoBuffer->StartAccess(bmdBufferAccessWrite) != S_OK) { videoBuffer->Release(); return nullptr; }
    
    void* frameData = nullptr;
    if (videoBuffer->GetBytes(&frameData) != S_OK) { 
        videoBuffer->EndAccess(bmdBufferAccessWrite); 
        videoBuffer->Release(); 
        return nullptr; 
    }
    
    // Return frame info
    *width = m_width;
    *height = m_height;
    int32_t rowBytes = 0;
    m_output->RowBytesForPixelFormat(m_pixelFormat, m_width, &rowBytes);
    *row_bytes = rowBytes;
    
    // Note: The caller should call commitFrame() after writing to the buffer
    return static_cast<uint8_t*>(frameData);
}

int DeckLinkSignalGen::commitFrame() {
    if (!m_frame) return -1;
    
    // Apply EOTF metadata if set
    if (m_eotfType >= 0) {
        int metadataResult = applyEOTFMetadata();
        if (metadataResult != 0) return metadataResult;
    }
    
    return 0;
}

int DeckLinkSignalGen::getDeviceCount() {
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

std::string DeckLinkSignalGen::getDeviceName(int deviceIndex) {
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
void DeckLinkSignalGen::cacheSupportedFormats() {
    if (!m_output) return;
    
    std::set<BMDPixelFormat> uniqueFormats;
    
    // Test common pixel formats against a standard display mode (1080p30)
    // Order by preference: 12-bit first, then 10-bit, then 8-bit
    BMDPixelFormat supportedFormats[] = {
        bmdFormat12BitRGB,
        bmdFormat10BitRGB,
        bmdFormat10BitYUV,
        bmdFormat10BitRGBX,
        bmdFormat10BitRGBXLE,
        bmdFormat8BitBGRA,
        bmdFormat8BitARGB,
        bmdFormat8BitYUV
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



int DeckLinkSignalGen::applyEOTFMetadata() {
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

int decklink_set_eotf_metadata(DeckLinkHandle handle, int eotf, uint16_t maxCLL, uint16_t maxFALL) {
    if (!handle) return -1;
    auto* signalGen = static_cast<DeckLinkSignalGen*>(handle);
    return signalGen->setEOTFMetadata(eotf, maxCLL, maxFALL);
}

int decklink_set_frame_data(DeckLinkHandle handle, const uint8_t* data, int width, int height, BMDPixelFormat pixel_format) {
    if (!handle || !data) return -1;
    auto* signalGen = static_cast<DeckLinkSignalGen*>(handle);
    return signalGen->setFrameData(data, width, height, pixel_format);
}

uint8_t* decklink_get_frame_buffer(DeckLinkHandle handle, int* width, int* height, int* row_bytes) {
    if (!handle || !width || !height || !row_bytes) return nullptr;
    auto* signalGen = static_cast<DeckLinkSignalGen*>(handle);
    return signalGen->getFrameBuffer(width, height, row_bytes);
}

int decklink_commit_frame(DeckLinkHandle handle) {
    if (!handle) return -1;
    auto* signalGen = static_cast<DeckLinkSignalGen*>(handle);
    return signalGen->commitFrame();
}

// Thin C wrapper implementation
extern "C" {

int decklink_get_device_count() {
    return DeckLinkSignalGen::getDeviceCount();
}

int decklink_get_device_name_by_index(int index, char* name, int name_size) {
    if (!name || name_size <= 0) return -1;
    
    std::string deviceName = DeckLinkSignalGen::getDeviceName(index);
    if (deviceName.empty()) return -1;
    
    strncpy(name, deviceName.c_str(), name_size - 1);
    name[name_size - 1] = '\0';
    return 0;
}

DeckLinkHandle decklink_open_output_by_index(int index) {
    DeckLinkSignalGen* signalGen = new DeckLinkSignalGen();
    if (signalGen->openDevice(index)) {
        return signalGen;
    }
    delete signalGen;
    return nullptr;
}

void decklink_close(DeckLinkHandle handle) {
    if (handle) {
    auto* signalGen = static_cast<DeckLinkSignalGen*>(handle);
    delete signalGen;
    }
}



int decklink_start_output(DeckLinkHandle handle) {
    if (!handle) return -1;
    auto* signalGen = static_cast<DeckLinkSignalGen*>(handle);
    return signalGen->startOutput();
}

int decklink_stop_output(DeckLinkHandle handle) {
    if (!handle) return -1;
    auto* signalGen = static_cast<DeckLinkSignalGen*>(handle);
    return signalGen->stopOutput();
}

int decklink_get_supported_pixel_format_count(DeckLinkHandle handle) {
    if (!handle) return 0;
    auto* signalGen = static_cast<DeckLinkSignalGen*>(handle);
    return static_cast<int>(signalGen->getSupportedPixelFormats().size());
}

int decklink_get_supported_pixel_format_name(DeckLinkHandle handle, int index, char* name, int name_size) {
    if (!handle || !name || name_size <= 0) return -1;
    auto* signalGen = static_cast<DeckLinkSignalGen*>(handle);
    
    std::vector<BMDPixelFormat> formats = signalGen->getSupportedPixelFormats();
    if (index < 0 || index >= static_cast<int>(formats.size())) return -1;
    
    std::string formatName = signalGen->getPixelFormatName(formats[index]);
    strncpy(name, formatName.c_str(), name_size - 1);
    name[name_size - 1] = '\0';
    return 0;
}

int decklink_set_pixel_format(DeckLinkHandle handle, int pixel_format_index) {
    if (!handle) return -1;
    auto* signalGen = static_cast<DeckLinkSignalGen*>(handle);
    return signalGen->setPixelFormat(pixel_format_index);
}

int decklink_get_pixel_format(DeckLinkHandle handle) {
    if (!handle) return -1;
    auto* signalGen = static_cast<DeckLinkSignalGen*>(handle);
    return signalGen->getPixelFormat();
}

static std::string g_driver_version;
static std::string g_sdk_version = BLACKMAGIC_DECKLINK_API_VERSION_STRING;

const char* decklink_get_driver_version() {
    static std::string version;
    if (!version.empty()) return version.c_str();
    
    IDeckLinkAPIInformation* apiInfo = CreateDeckLinkAPIInformationInstance();
    if (apiInfo) {
        int64_t versionInt = 0;
        if (apiInfo->GetInt(BMDDeckLinkAPIVersion, &versionInt) == S_OK) {
            int major = (versionInt >> 24) & 0xFF;
            int minor = (versionInt >> 16) & 0xFF;
            int patch = (versionInt >> 8) & 0xFF;
            char buf[32];
            snprintf(buf, sizeof(buf), "%d.%d.%d", major, minor, patch);
            version = buf;
        } else {
            version = "unknown";
        }
        apiInfo->Release();
    } else {
        version = "unavailable";
    }
    return version.c_str();
}

const char* decklink_get_sdk_version() {
    return g_sdk_version.c_str();
}

} 