#pragma once

#include "DeckLinkAPI.h"
#include <memory>
#include <string>
#include <vector>
#include <set>

// Wrapper definitions for versioned symbols
extern "C" {
    IDeckLinkIterator* CreateDeckLinkIteratorInstance_0004(void);
    IDeckLinkDiscovery* CreateDeckLinkDiscoveryInstance_0003(void);
}

#define CreateDeckLinkIteratorInstance CreateDeckLinkIteratorInstance_0004
#define CreateDeckLinkDiscoveryInstance CreateDeckLinkDiscoveryInstance_0003

// C-style API for Python
extern "C" {
    // Device management
    typedef struct DeckLinkDevice DeckLinkDevice;
    typedef struct DeckLinkOutput DeckLinkOutput;
    typedef struct DeckLinkFrame DeckLinkFrame;
    
    // Error codes
    #define DECKLINK_SUCCESS 0
    #define DECKLINK_ERROR_NO_DEVICE -1
    #define DECKLINK_ERROR_INIT_FAILED -2
    #define DECKLINK_ERROR_OUTPUT_FAILED -3
    #define DECKLINK_ERROR_FRAME_FAILED -4
    
    // Device enumeration
    int decklink_get_device_count();
    DeckLinkDevice* decklink_get_device(int index);
    void decklink_release_device(DeckLinkDevice* device);
    
    // Device info
    const char* decklink_get_device_name(DeckLinkDevice* device);
    int decklink_has_output(DeckLinkDevice* device);
    
    // Output management
    DeckLinkOutput* decklink_create_output(DeckLinkDevice* device);
    void decklink_release_output(DeckLinkOutput* output);
    
    // Video modes
    int decklink_get_mode_count(DeckLinkOutput* output);
    int decklink_get_mode_info(DeckLinkOutput* output, int index, 
                              int* width, int* height, double* frameRate, 
                              char* name, int nameSize);
    
    // Pixel formats
    int decklink_get_pixel_format_count(DeckLinkOutput* output);
    int decklink_get_pixel_format_info(DeckLinkOutput* output, int index,
                                      int* formatId, char* name, int nameSize);
    
    // Video output
    int decklink_enable_output(DeckLinkOutput* output, int displayMode);
    int decklink_disable_output(DeckLinkOutput* output);
    
    // Frame creation and output
    DeckLinkFrame* decklink_create_frame(DeckLinkOutput* output, 
                                        int width, int height, int pixelFormat);
    int decklink_fill_frame_color(DeckLinkFrame* frame, 
                                 unsigned char r, unsigned char g, unsigned char b);
    int decklink_schedule_frame(DeckLinkOutput* output, DeckLinkFrame* frame,
                               long long streamTime, long long frameDuration, long long timeScale);
    int decklink_start_playback(DeckLinkOutput* output, long long startTime, 
                               long long timeScale, double playbackSpeed);
    int decklink_stop_playback(DeckLinkOutput* output);
    void decklink_release_frame(DeckLinkFrame* frame);
    
    // Status
    int decklink_is_playing(DeckLinkOutput* output);
    long long decklink_get_current_time(DeckLinkOutput* output);
}

// C++ wrapper classes (internal implementation)
class DeckLinkDeviceWrapper {
public:
    DeckLinkDeviceWrapper(IDeckLink* device);
    ~DeckLinkDeviceWrapper();
    
    std::string getName() const;
    bool hasOutput() const;
    IDeckLink* getDevice() const { return m_device; }
    
private:
    IDeckLink* m_device;
    std::string m_name;
};

class DeckLinkOutputWrapper {
public:
    DeckLinkOutputWrapper(IDeckLinkOutput* output);
    ~DeckLinkOutputWrapper();
    
    int enableOutput(BMDDisplayMode displayMode);
    int disableOutput();
    int createFrame(int width, int height, BMDPixelFormat pixelFormat, 
                   IDeckLinkMutableVideoFrame** frame);
    int scheduleFrame(IDeckLinkVideoFrame* frame, BMDTimeValue streamTime,
                     BMDTimeValue frameDuration, BMDTimeScale timeScale);
    int startPlayback(BMDTimeValue startTime, BMDTimeScale timeScale, double playbackSpeed);
    int stopPlayback();
    bool isPlaying();
    BMDTimeValue getCurrentTime();
    
    std::vector<BMDDisplayMode> getSupportedModes();
    std::vector<BMDPixelFormat> getSupportedPixelFormats();
    
private:
    IDeckLinkOutput* m_output;
    bool m_enabled;
    bool m_playing;
};

class DeckLinkFrameWrapper {
public:
    DeckLinkFrameWrapper(IDeckLinkMutableVideoFrame* frame);
    ~DeckLinkFrameWrapper();
    
    int fillColor(unsigned char r, unsigned char g, unsigned char b);
    IDeckLinkVideoFrame* getFrame() const { return m_frame; }
    
private:
    IDeckLinkMutableVideoFrame* m_frame;
    int m_width;
    int m_height;
    BMDPixelFormat m_pixelFormat;
};

// C++ Implementation Classes
class DeckLinkColorPatch {
public:
    DeckLinkColorPatch();
    ~DeckLinkColorPatch();
    
    // Device management
    bool openDevice(int deviceIndex);
    void closeDevice();
    
    // Color and frame management
    int setColor(uint16_t r, uint16_t g, uint16_t b);
    int startOutput();
    int stopOutput();
    
    // Pixel format management
    std::vector<BMDPixelFormat> getSupportedPixelFormats();
    int setPixelFormat(int pixelFormatIndex);
    int getPixelFormat() const;
    std::string getPixelFormatName(BMDPixelFormat format) const;
    
    // EOTF metadata management
    int setEOTFMetadata(int eotf, uint16_t maxCLL, uint16_t maxFALL);
    
    // Device enumeration (static)
    static int getDeviceCount();
    static std::string getDeviceName(int deviceIndex);
    
private:
    // Core DeckLink objects
    IDeckLink* m_device;
    IDeckLinkOutput* m_output;
    IDeckLinkMutableVideoFrame* m_frame;
    
    // Configuration
    int m_width;
    int m_height;
    uint16_t m_r, m_g, m_b;
    bool m_outputEnabled;
    BMDPixelFormat m_pixelFormat;
    
    // HDR metadata
    int m_eotfType;
    uint16_t m_maxCLL;
    uint16_t m_maxFALL;
    
    // Cached supported formats
    std::vector<BMDPixelFormat> m_supportedFormats;
    bool m_formatsCached;
    
    // Private helper methods
    void cacheSupportedFormats();
    int fillFrameWithColor();
    int applyEOTFMetadata();
    uint32_t convertRGBToPixelFormat(int r, int g, int b, BMDPixelFormat format);
    void logFrameInfo(const char* context);
};

// Thin C wrapper for ctypes compatibility
#ifdef __cplusplus
extern "C" {
#endif

typedef void* DeckLinkHandle;

// Device enumeration
int decklink_get_device_count();
int decklink_get_device_name_by_index(int index, char* name, int name_size);

// Device management
DeckLinkHandle decklink_open_output_by_index(int index);
void decklink_close(DeckLinkHandle handle);

// Color and output control
int decklink_set_color(DeckLinkHandle handle, uint16_t r, uint16_t g, uint16_t b);
int decklink_start_output(DeckLinkHandle handle);
int decklink_stop_output(DeckLinkHandle handle);

// Pixel format management
int decklink_get_supported_pixel_format_count(DeckLinkHandle handle);
int decklink_get_supported_pixel_format_name(DeckLinkHandle handle, int index, char* name, int name_size);
int decklink_set_pixel_format(DeckLinkHandle handle, int pixel_format_index);
int decklink_get_pixel_format(DeckLinkHandle handle);

// EOTF metadata control
int decklink_set_eotf_metadata(DeckLinkHandle handle, int eotf, uint16_t maxCLL, uint16_t maxFALL);

#ifdef __cplusplus
}
#endif 