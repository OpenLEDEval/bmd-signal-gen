#pragma once

#include "DeckLinkAPI.h"
#include <memory>
#include <string>
#include <vector>
#include <set>

// Handle type for C API
typedef void* DeckLinkHandle;

// Wrapper definitions for versioned symbols
extern "C" {
    IDeckLinkIterator* CreateDeckLinkIteratorInstance_0004(void);
    IDeckLinkDiscovery* CreateDeckLinkDiscoveryInstance_0003(void);
    IDeckLinkAPIInformation* CreateDeckLinkAPIInformationInstance_0001(void);
}

#define CreateDeckLinkIteratorInstance CreateDeckLinkIteratorInstance_0004
#define CreateDeckLinkDiscoveryInstance CreateDeckLinkDiscoveryInstance_0003
#define CreateDeckLinkAPIInformationInstance CreateDeckLinkAPIInformationInstance_0001

// Error codes
#define DECKLINK_SUCCESS 0
#define DECKLINK_ERROR_NO_DEVICE -1
#define DECKLINK_ERROR_INIT_FAILED -2
#define DECKLINK_ERROR_OUTPUT_FAILED -3
#define DECKLINK_ERROR_FRAME_FAILED -4

// Complete HDR metadata structure (matching SignalGenHDR sample)
struct GamutChromaticities {
    double RedX;
    double RedY;
    double GreenX;
    double GreenY;
    double BlueX;
    double BlueY;
    double WhiteX;
    double WhiteY;
};

struct HDRMetadata {
    int64_t EOTF;
    GamutChromaticities referencePrimaries;
    double maxDisplayMasteringLuminance;
    double minDisplayMasteringLuminance;
    double maxCLL;
    double maxFALL;
};

// C++ Implementation Class
class DeckLinkSignalGen {
public:
    DeckLinkSignalGen();
    ~DeckLinkSignalGen();
    
    // Output control
    int startOutput();
    int stopOutput();
    
    // Frame management
    int createFrame();
    int displayFrameSync();
    
    // Pixel format management
    int setPixelFormat(BMDPixelFormat pixelFormat);
    BMDPixelFormat getPixelFormat() const;
    
    // Complete HDR metadata management
    int setHDRMetadata(const HDRMetadata& metadata);
    
    // Frame data management
    int setFrameData(const uint16_t* data, int width, int height);
    
    // Device enumeration (static)
    static int getDeviceCount();
    static std::string getDeviceName(int deviceIndex);
    
    // Public access for C wrapper
    void cacheSupportedFormats();
    std::vector<BMDPixelFormat>& getSupportedFormats() { return m_supportedFormats; }
    
    // Core DeckLink objects (made public for C wrapper access)
    IDeckLink* m_device;
    IDeckLinkOutput* m_output;
    IDeckLinkMutableVideoFrame* m_frame;

private:
    // Configuration
    int m_width;
    int m_height;
    bool m_outputEnabled;
    BMDPixelFormat m_pixelFormat;
    
    // Complete HDR metadata
    HDRMetadata m_hdrMetadata;
    
    // Cached supported formats
    std::vector<BMDPixelFormat> m_supportedFormats;
    bool m_formatsCached;
    
    // Pending frame data
    std::vector<uint16_t> m_pendingFrameData;
    
    // Private helper methods
    int applyHDRMetadata();
    void logFrameInfo(const char* context);
};

// Thin C wrapper for ctypes compatibility
#ifdef __cplusplus
extern "C" {
#endif

// Device enumeration
int decklink_get_device_count();
int decklink_get_device_name_by_index(int index, char* name, int name_size);

// Device management
DeckLinkHandle decklink_open_output_by_index(int index);
void decklink_close(DeckLinkHandle handle);

// Output control
int decklink_start_output(DeckLinkHandle handle);
int decklink_stop_output(DeckLinkHandle handle);

// Frame management
int decklink_create_frame_from_data(DeckLinkHandle handle);

// Pixel format management
int decklink_get_supported_pixel_format_count(DeckLinkHandle handle);
int decklink_get_supported_pixel_format_name(DeckLinkHandle handle, int index, char* name, int name_size);
int decklink_set_pixel_format(DeckLinkHandle handle, uint32_t pixel_format_code);
uint32_t decklink_get_pixel_format(DeckLinkHandle handle);

// Complete HDR metadata control
int decklink_set_hdr_metadata(DeckLinkHandle handle, const HDRMetadata* metadata);

// Frame data management
int decklink_set_frame_data(DeckLinkHandle handle, const uint16_t* data, int width, int height);

// Synchronous display
int decklink_display_frame_sync(DeckLinkHandle handle);

// HDR capability detection
bool decklink_device_supports_hdr(DeckLinkHandle handle);

// Version info
const char* decklink_get_driver_version();
const char* decklink_get_sdk_version();

#ifdef __cplusplus
}
#endif

// C++ wrapper functions (not in extern "C" block)
int decklink_get_supported_pixel_format_count(DeckLinkHandle handle);
int decklink_get_supported_pixel_format_name(DeckLinkHandle handle, int index, char* name, int name_size); 