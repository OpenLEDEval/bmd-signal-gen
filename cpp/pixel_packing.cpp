#include "pixel_packing.h"
#include <algorithm>
#include <iostream>
#include <cstring>
#include <vector>
#include <bit>
#include <numeric>
#include <cstdint>

/*
 * Pixel Packing for Blackmagic DeckLink API
 * 
 * This file contains the implementation of various pixel packing schemes
 * used by Blackmagic DeckLink devices. Each function handles the specific
 * bit depth and packing requirements per the DeckLink SDK documentation
 * section 3.4.
 * 
 * INPUT RANGES:
 * - 8-bit functions: Expect 8-bit values (0-255) in a 16-bit container
 * - 10-bit functions: Expect 10-bit values (0-1023) in a 16-bit container
 * - 12-bit function: Expect 12-bit values (0-4095) in a 16-bit container
 * 
 * All functions include range checking and will clamp values to valid ranges.
 * These functions are focused purely on packing existing image data.
 * Specifically, the YUV packing functions simply pack the data, they do not
 * perform any RGB to YUV conversion
 */

/**
 * bmdFormat8BitYUV : '2vuy' 4:2:2 Representation
 * 
 * Four 8-bit unsigned components (CCIR 601) are packed into one 32-bit little-
 * endian word.
 * 
 * int framesize = (Width * 16 / 8) * Height
 *               = rowbytes * Height
 * 
 * In this format, two pixels fits into 32 bits or 4 bytes, so one pixel fits
 * into 16 bits or 2 bytes.
 * 
 * For the row bytes calculation, the image width is multiplied by the number of
 * bytes per pixel.
 * 
 * For the frame size calculation, the row bytes are simply multiplied by the
 * number of rows in the frame.
 * 
 * Note that in the source image, Y U and V are defined per pixel, however U and
 * V are discarded for every second pixel
 * 
 * @param destData Pointer to destination frame buffer
 * @param srcY Pointer to source Y channel data (8-bit, 0-255)
 * @param srcU Pointer to source U channel data (8-bit, 0-255)
 * @param srcV Pointer to source V channel data (8-bit, 0-255)
 * @param width Frame width in pixels
 * @param height Frame height in pixels
 * @param rowBytes Bytes per row (including padding)
 */
void pack_8bpc_yuv_image(
    void* destData,
    const uint16_t* srcY, const uint16_t* srcU, const uint16_t* srcV,
    uint16_t width, uint16_t height,
    uint16_t rowBytes) {
    
    uint8_t* bytes = static_cast<uint8_t*>(destData);
    
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x += 2) {
            int srcIndex = y * width + x;
            int destIndex = y * rowBytes + (x * 2); // 2 bytes per pixel in YUV 4:2:2
            
            uint8_t y_val = std::min(srcY[srcIndex], static_cast<uint16_t>(255));
            uint8_t u = std::min(srcU[srcIndex], static_cast<uint16_t>(255));
            uint8_t v = std::min(srcV[srcIndex], static_cast<uint16_t>(255));

            // Pack into YUV 4:2:2 format: Y'0U0Y'1V0
            // For even pixels: U0 Y0 V0 Y1
            // For odd pixels:  U1 Y2 V1 Y3
            if (x % 2 == 0) {
                // Even pixel: store U and Y'0
                bytes[destIndex] = v;
                bytes[destIndex + 1] = y_val;
            } else {
                // Odd pixel: store U and Y'1
                bytes[destIndex] = u;
                bytes[destIndex + 1] = y_val;
            }
        }
    }
    
    std::cerr << "[PixelPacking] 8-bit YUV image packed: " << width << "x" << height << std::endl;
}


/**
 * Pack 8-bit RGB image data into BGRA/ARGB format
 * 
 * Packs existing 8-bit RGB image data into BGRA or ARGB format.
 * 
 * @param destData Pointer to destination frame buffer
 * @param srcR Pointer to source red channel data (8-bit, 0-255)
 * @param srcG Pointer to source green channel data (8-bit, 0-255)
 * @param srcB Pointer to source blue channel data (8-bit, 0-255)
 * @param width Frame width in pixels
 * @param height Frame height in pixels
 * @param rowBytes Bytes per row (including padding)
 * @param isBGRA true for BGRA format, false for ARGB format
 */
void pack_8bpc_rgb_image(
    void* destData,
    const uint16_t* srcR, const uint16_t* srcG, const uint16_t* srcB,
    uint16_t width, uint16_t height,
    uint16_t rowBytes,
    bool isBGRA) {
    /*
     * Pack 8-bit RGB image data into BGRA/ARGB format
     * 
     * Packs existing 8-bit RGB image data into BGRA or ARGB format.
     */
    
    uint32_t* pixels = static_cast<uint32_t*>(destData);
    
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            int srcIndex = y * width + x;
            int destIndex = y * (rowBytes / 4) + x;
            
            uint8_t r = srcR[srcIndex];
            uint8_t g = srcG[srcIndex];
            uint8_t b = srcB[srcIndex];
            
            uint32_t color;
            if (isBGRA) {
                // BGRA format: AABBGGRR
                color = (0xFF << 24) | (r << 16) | (g << 8) | b;
            } else {
                // ARGB format: AARRGGBB  
                color = (0xFF << 24) | (b << 16) | (g << 8) | r;
            }
            
            pixels[destIndex] = color;
        }
    }
    
    std::cerr << "[PixelPacking] 8-bit RGB image packed: " << width << "x" << height 
              << " into " << (isBGRA ? "BGRA" : "ARGB") << " format" << std::endl;
}

/**
 * bmdFormat10BitRGB : 'r210' 4:4:4 raw
 * 
 * Three 10-bit unsigned components are packed into one 32-bit big-endian word.
 * 
 * int framesize = ((Width + 63) / 64) * 256 * Height
 *               = rowbytes * Height
 * 
 * In this format each line of video must be aligned a 256 byte boundary. One
 * pixel fits into 4 bytes so 64 pixels fit into 256 bytes.
 * 
 * For the row bytes calculation, the image width is rounded to the nearest 64
 * pixel boundary and multiplied by 256.
 * 
 * For the frame size calculation, the row bytes are simply multiplied by the
 * number of rows in the frame. 
 * 
 * @param destData Pointer to destination frame buffer
 * @param srcR Pointer to source red channel data (10-bit, 0-1023)
 * @param srcG Pointer to source green channel data (10-bit, 0-1023)
 * @param srcB Pointer to source blue channel data (10-bit, 0-1023)
 * @param width Frame width in pixels
 * @param height Frame height in pixels
 * @param rowBytes Bytes per row (including padding)
 */
void pack_10bpc_rgb_image(
    void* destData,
    const uint16_t* srcR, const uint16_t* srcG, const uint16_t* srcB,
    uint16_t width, uint16_t height,
    uint16_t rowBytes) {
    
    uint32_t* pixels = static_cast<uint32_t*>(destData);
    
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            int srcIndex = y * width + x;
            int destIndex = y * (rowBytes / 4) + x;
            
            uint16_t r = srcR[srcIndex];
            uint16_t g = srcG[srcIndex];
            uint16_t b = srcB[srcIndex];
            
            // Pack using Blackmagic's reference implementation in ColorBars.cpp
            // Refer to DeckLink SDK Manual, section 2.7.4 for packing structure
            uint32_t pixel = ((b & 0x3FC) << 22) | ((g & 0x0FC) << 16) | ((b & 0xC00) << 6)
                           | ((r & 0x03C) << 10) | (g & 0xF00) | ((r & 0xFC0) >> 6);

            pixels[destIndex] = pixel;
        }
    }
    
    std::cerr << "[PixelPacking] big-endian 10-bit RGB image packed: "
              << width << "x" << height << std::endl;
}

/**
 * bmdFormat12BitRGBLE : 'R12L'
 * 
 * Little-endian RGB 12-bit per component with full range (0-4095). Packed as
 * 12-bit per component.
 * 
 * This 12-bit pixel format is compatible with SMPTE 268M Digital Moving-Picture
 * Exchange version 1, Annex C, Method C4 packing.
 * 
 * int framesize = ((Width * 36) / 8) * Height
 *               = rowBytes * Height
 * 
 * In this format, 8 pixels fit into 36 bytes.
 *
 * @param destData Pointer to destination frame buffer
 * @param srcR Pointer to source red channel data (12-bit, 0-4095)
 * @param srcG Pointer to source green channel data (12-bit, 0-4095)
 * @param srcB Pointer to source blue channel data (12-bit, 0-4095)
 * @param width Frame width in pixels
 * @param height Frame height in pixels
 * @param rowBytes Bytes per row (including padding)
 */
void pack_12bpc_rgble_image(
    void* destData,
    const uint16_t* srcR, const uint16_t* srcG, const uint16_t* srcB,
    uint16_t width, uint16_t height,
    uint16_t rowBytes) {
    
    uint32_t* pixels = static_cast<uint32_t*>(destData);
    
    if (std::endian::native != std::endian::little) {
        std::cerr << "[PixelPacking] System is not little endian, but 12b packing implementation likely depends on it for byte ordering. Proceed with caution" << std::endl;
    } 

    std::cerr << "[PixelPacking] Packing little-endian 12-bit RGB image: " << width << "x"
              << height << ", rowBytes: " << rowBytes << std::endl;
    
    for (int y = 0; y < height; y++) {
        uint32_t* row = pixels + (y * (rowBytes / 4));
        for (int x = 0; x < width; x += 8) {
            uint32_t* groupPtr = row + ((x / 8) * 9);
            // Based on Blackmagic's reference implementation in ColorBars.cpp
            int base = y * width + x;
            groupPtr[0] = ((srcB[base + 0] & 0x0FF) << 24) | ((srcG[base + 0] & 0xFFF) << 12) | (srcR[base + 0] & 0xFFF);
            groupPtr[1] = ((srcB[base + 1] & 0x00F) << 28) | ((srcG[base + 1] & 0xFFF) << 16) | ((srcR[base + 1] & 0xFFF) << 4) | ((srcB[base + 0] & 0xF00) >> 8);
            groupPtr[2] = ((srcG[base + 2] & 0xFFF) << 20) | ((srcR[base + 2] & 0xFFF) << 8) | ((srcB[base + 1] & 0xFF0) >> 4);
            groupPtr[3] = ((srcG[base + 3] & 0x0FF) << 24) | ((srcR[base + 3] & 0xFFF) << 12) | (srcB[base + 2] & 0xFFF);
            groupPtr[4] = ((srcG[base + 4] & 0x00F) << 28) | ((srcR[base + 4] & 0xFFF) << 16) | ((srcB[base + 3] & 0xFFF) << 4) | ((srcG[base + 3] & 0xF00) >> 8);
            groupPtr[5] = ((srcR[base + 5] & 0xFFF) << 20) | ((srcB[base + 4] & 0xFFF) << 8) | ((srcG[base + 4] & 0xFF0) >> 4);
            groupPtr[6] = ((srcR[base + 6] & 0x0FF) << 24) | ((srcB[base + 5] & 0xFFF) << 12) | (srcG[base + 5] & 0xFFF);
            groupPtr[7] = ((srcR[base + 7] & 0x00F) << 28) | ((srcB[base + 6] & 0xFFF) << 16) | ((srcG[base + 6] & 0xFFF) << 4) | ((srcR[base + 6] & 0xF00) >> 8);
            groupPtr[8] = ((srcB[base + 7] & 0xFFF) << 20) | ((srcG[base + 7] & 0xFFF) << 8) | ((srcR[base + 7] & 0xFF0) >> 4);
        }
    }
    
    std::cerr << "[PixelPacking] little-endian 12-bit RGB image packed successfully" << std::endl;
}

// Clamp a channel buffer to a given bit depth
static void clamp_channel(std::vector<uint16_t>& channel, int bits) {
    uint16_t maxval = (1u << bits) - 1;
    for (auto& v : channel) {
        if (v > maxval) v = maxval;
    }
}

// Clamp all channels to a given bit depth
static void clamp_image_channels(std::vector<uint16_t>& r, std::vector<uint16_t>& g, std::vector<uint16_t>& b, int bits) {
    clamp_channel(r, bits);
    clamp_channel(g, bits);
    clamp_channel(b, bits);
}

int pack_pixel_format(
    void* destData,
    BMDPixelFormat pixelFormat,
    const uint16_t* srcData,
    uint16_t width, uint16_t height,
    uint16_t rowBytes
 ) {
    // Extract RGB channels from the raw data (3 uint16_t per pixel: R, G, B)
    std::vector<uint16_t> r_channel(width * height);
    std::vector<uint16_t> g_channel(width * height);
    std::vector<uint16_t> b_channel(width * height);
    
    for (int i = 0; i < width * height; i++) {
        r_channel[i] = srcData[i * 3 + 0];
        g_channel[i] = srcData[i * 3 + 1];
        b_channel[i] = srcData[i * 3 + 2];
    }

    // Pack the data according to the pixel format
    switch (pixelFormat) {
        case bmdFormat8BitBGRA:
            clamp_image_channels(r_channel, g_channel, b_channel, 8);
            pack_8bpc_rgb_image(
                destData,
                r_channel.data(), g_channel.data(), b_channel.data(),
                width, height,
                rowBytes,
                true);
            break;
        case bmdFormat8BitARGB:
            clamp_image_channels(r_channel, g_channel, b_channel, 8);
            pack_8bpc_rgb_image(
                destData,
                r_channel.data(), g_channel.data(), b_channel.data(),
                width, height,
                rowBytes,
                false);
            break;
        case bmdFormat10BitRGB:
            clamp_image_channels(r_channel, g_channel, b_channel, 10);
            pack_10bpc_rgb_image(
                destData,
                r_channel.data(), g_channel.data(), b_channel.data(),
                width, height,
                rowBytes);
            break;
        case bmdFormat12BitRGBLE:
            clamp_image_channels(r_channel, g_channel, b_channel, 12);
            pack_12bpc_rgble_image(
                destData,
                r_channel.data(), g_channel.data(), b_channel.data(),
                width, height,
                rowBytes);
            break;
        default:
            std::cerr << "[DeckLink] Unsupported pixel format: 0x" << std::hex << pixelFormat << std::dec << std::endl;
            return -8;
    }
    return 0;
 }