#include "pixel_packing.h"
#include <algorithm>
#include <iostream>
#include <cstring>
#include <vector>
#include <bit>
#include <numeric>

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
 * bmdFormat10BitRGB : ‘r210’ 4:4:4 raw
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
            
            uint16_t r = std::min(srcR[srcIndex], static_cast<uint16_t>(1023));
            uint16_t g = std::min(srcG[srcIndex], static_cast<uint16_t>(1023));
            uint16_t b = std::min(srcB[srcIndex], static_cast<uint16_t>(1023));
            
            uint32_t pixel = (b & 0x000F) << 24 | (b & 0x0300) << 8
                           | (g & 0x003F) << 18 | (g & 0x03C0) << 2
                           | (r & 0x000F) << 12 | (r & 0x03F0) >> 4;

            pixels[destIndex] = pixel;
        }
    }
    
    std::cerr << "[PixelPacking] big-endian 10-bit RGB image packed: "
              << width << "x" << height << std::endl;
}

/**
 * Pack 10-bit YUV image data into 10-bit YUV format
 * 
 * Packs existing 10-bit YUV image data into 10-bit YUV format.
 * 
 * @param destData Pointer to destination frame buffer
 * @param srcY Pointer to source Y channel data (10-bit, 0-1023)
 * @param srcU Pointer to source U channel data (10-bit, 0-1023)
 * @param srcV Pointer to source V channel data (10-bit, 0-1023)
 * @param width Frame width in pixels
 * @param height Frame height in pixels
 * @param rowBytes Bytes per row (including padding)
 */
void pack_10bpc_yuv_image(void* destData, const uint16_t* srcY, const uint16_t* srcU, const uint16_t* srcV,
                         uint16_t width, uint16_t height, uint16_t rowBytes) {
    /*
     * Pack 10-bit YUV image data into 10-bit YUV format
     * 
     * Packs existing 10-bit YUV image data into 10-bit YUV format.
     * This function separates the packing logic from frame filling.
     */
    
    uint32_t* pixels = static_cast<uint32_t*>(destData);
    
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            int srcIndex = y * width + x;
            int destIndex = y * (rowBytes / 4) + x;
            
            uint16_t y_val = std::min(srcY[srcIndex], static_cast<uint16_t>(1023));
            uint16_t u = std::min(srcU[srcIndex], static_cast<uint16_t>(1023));
            uint16_t v = std::min(srcV[srcIndex], static_cast<uint16_t>(1023));
            
            // Pack into 32-bit word: U[9:0] | Y[9:0] << 10 | V[9:0] << 20
            uint32_t color = (u & 0x3FF) | ((y_val & 0x3FF) << 10) | ((v & 0x3FF) << 20);
            
            pixels[destIndex] = color;
        }
    }
    
    std::cerr << "[PixelPacking] 10-bit YUV image packed: " << width << "x" << height << std::endl;
}

/**
 * Swizzle a portion of two 12-bit color channels into a single byte
 * 
 * Takes two 12-bit color channels and swizzles a portion of them into a single
 * byte with the following format:
 * low 4 bits of channel B, high 4 bits of channel A
 * 
 * @param channelA First 12-bit channel (0-4095)
 * @param channelB Second 12-bit channel (0-4095)
 * @return Swizzled byte with low 4 bits of A and high 4 bits of B
 */
static uint8_t swizzle_two_12(uint16_t channelA, uint16_t channelB) {
    // Extract 4 bits from each channel
    uint8_t b_high_4bits = (channelB & 0xF0) >> 4;  // channelB[11:8]
    uint8_t a_low_4bits = channelA & 0x0F;  // channelA[3:0]
    
    // Swizzle into single byte: [A_low_4bits][B_high_4bits]
    // This puts A's low 4 bits in the high 4 bits of the output byte
    return (a_low_4bits << 4) | b_high_4bits;
}

/**
 * Extract the high 8 bits from a 12-bit color channel
 * 
 * Takes a 12-bit color channel and extracts the high 8 bits (bits 11-4)
 * 
 * @param channel 12-bit channel (0-4095)
 * @return High 8 bits of the channel (bits 11-4)
 */
static uint8_t high_8_of_12(uint16_t channel) {
    return (channel >> 4) & 0xFF;
}

/**
 * Extract the low 8 bits from a 12-bit color channel
 * 
 * Takes a 12-bit color channel and extracts the low 8 bits (bits 7-0)
 * 
 * @param channel 12-bit channel (0-4095)
 * @return Low 8 bits of the channel (bits 7-0)
 */
static uint8_t low_8_of_12(uint16_t channel) {
    return channel & 0xFF;
}

/**
 * Helper function to pack 8 pixels into 36 bytes
 * bmdFormat12BitRGB : 'R12B'
 * Big-endian RGB 12-bit per component with full range (0-4095).
 * Packed as 12-bit per component.
 * This 12-bit pixel format is compatible with SMPTE 268M Digital
 * Moving-Picture Exchange version 1, Annex C, Method C4 packing.
 * int framesize = ((Width * 36) / 8) * Height
 *               = rowbytes * Height
 * In this format, 8 pixels fit into 36 bytes.
 */
static void pack_8_12bpc_pixels_into_36_bytes(uint8_t* groupPtr, 
                                       const uint16_t r_channels[8], 
                                       const uint16_t g_channels[8], 
                                       const uint16_t b_channels[8]) {
    /**
     * INPUT:
     * - groupPtr: Pointer to 36-byte destination buffer
     * - r_channels[8]: Array of 8 red channel values (12-bit each, 0-4095)
     * - g_channels[8]: Array of 8 green channel values (12-bit each, 0-4095)
     * - b_channels[8]: Array of 8 blue channel values (12-bit each, 0-4095)
     */
    
    // word 0
    groupPtr[3] = low_8_of_12(r_channels[0]);
    groupPtr[2] = swizzle_two_12(g_channels[0], r_channels[0]);
    groupPtr[1] = high_8_of_12(g_channels[0]);
    groupPtr[0] = low_8_of_12(b_channels[0]);

    // word 1
    groupPtr[7] = swizzle_two_12(r_channels[1], b_channels[0]);
    groupPtr[6] = high_8_of_12(r_channels[1]);
    groupPtr[5] = low_8_of_12(g_channels[1]);
    groupPtr[4] = swizzle_two_12(b_channels[1], g_channels[1]);

    // word 2
    groupPtr[11] = high_8_of_12(b_channels[1]);
    groupPtr[10] = low_8_of_12(r_channels[2]);
    groupPtr[9] = swizzle_two_12(g_channels[2], r_channels[2]);
    groupPtr[8] = high_8_of_12(g_channels[2]);

    // word 3
    groupPtr[15] = low_8_of_12(b_channels[2]);
    groupPtr[14] = swizzle_two_12(r_channels[3], b_channels[2]);
    groupPtr[13] = high_8_of_12(r_channels[3]);
    groupPtr[12] = low_8_of_12(g_channels[3]);

    // word 4
    groupPtr[19] = swizzle_two_12(b_channels[3], g_channels[3]);
    groupPtr[18] = high_8_of_12(b_channels[3]);
    groupPtr[17] = low_8_of_12(r_channels[4]);
    groupPtr[16] = swizzle_two_12(g_channels[4], r_channels[4]);

    // word 5
    groupPtr[23] = high_8_of_12(g_channels[4]);
    groupPtr[22] = low_8_of_12(b_channels[4]);
    groupPtr[21] = swizzle_two_12(r_channels[5], b_channels[4]);
    groupPtr[20] = high_8_of_12(r_channels[5]);
    
    // word 6
    groupPtr[27] = low_8_of_12(g_channels[5]);
    groupPtr[26] = swizzle_two_12(b_channels[5], g_channels[5]);
    groupPtr[25] = high_8_of_12(b_channels[5]);
    groupPtr[24] = low_8_of_12(r_channels[6]);

    // word 7
    groupPtr[31] = swizzle_two_12(g_channels[6], r_channels[6]);
    groupPtr[30] = high_8_of_12(g_channels[6]);
    groupPtr[29] = low_8_of_12(b_channels[6]);
    groupPtr[28] = swizzle_two_12(r_channels[7], b_channels[6]);

    // word 8
    groupPtr[35] = high_8_of_12(r_channels[7]);
    groupPtr[34] = low_8_of_12(g_channels[7]);
    groupPtr[33] = swizzle_two_12(b_channels[7], g_channels[7]);
    groupPtr[32] = high_8_of_12(b_channels[7]);
}

/**
 * bmdFormat12BitRGB : 'R12B'
 * 
 * Big-endian RGB 12-bit per component with full range (0-4095). Packed as
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
void pack_12bpc_rgb_image(
    void* destData,
    const uint16_t* srcR, const uint16_t* srcG, const uint16_t* srcB,
    uint16_t width, uint16_t height,
    uint16_t rowBytes) {
    
    uint8_t* bytes = static_cast<uint8_t*>(destData);
    
    std::cerr << "[PixelPacking] Packing big-endian 12-bit RGB image: " << width << "x"
              << height << ", rowBytes: " << rowBytes << std::endl;
    
    for (int y = 0; y < height; y++) {
        uint8_t* row = bytes + (y * rowBytes);
        
        // Process pixels in groups of 8 (36 bytes per group)
        for (int x = 0; x < width; x += 8) {
            // Base address for this pixel group (36 bytes)
            uint8_t* groupPtr = row + ((x / 8) * 36);
            
            // Prepare arrays for the 8 pixels in this group
            uint16_t r_channels[8], g_channels[8], b_channels[8];
            
            // Fill the arrays with image data
            for (int i = 0; i < 8; i++) {
                int pixelX = x + i;
                if (pixelX < width) {
                    int srcIndex = y * width + pixelX;
                    r_channels[i] = std::min(srcR[srcIndex], static_cast<uint16_t>(4095));
                    g_channels[i] = std::min(srcG[srcIndex], static_cast<uint16_t>(4095));
                    b_channels[i] = std::min(srcB[srcIndex], static_cast<uint16_t>(4095));
                } else {
                    // Pad with zeros if we're at the end of a row
                    r_channels[i] = 0;
                    g_channels[i] = 0;
                    b_channels[i] = 0;
                }
            }
            
            // Use the helper function to pack 8 pixels into 36 bytes
            pack_8_12bpc_pixels_into_36_bytes(
                groupPtr,
                r_channels, g_channels, b_channels);
        }
    }
    
    std::cerr << "[PixelPacking] big endian 12-bit RGB image packed successfully" << std::endl;
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
    
    if (std::endian::native == std::endian::little) {
        std::cout << "[PixelPacking] System is little endian" << std::endl;
    } else if (std::endian::native == std::endian::big) {
        std::cout << "[PixelPacking] System is big endian" << std::endl;
    } else {
        std::cout << "[PixelPacking] System endianness is mixed or unknown." << std::endl;
    }

    // Pack the data according to the pixel format
    switch (pixelFormat) {
        case bmdFormat8BitBGRA: {
            pack_8bpc_rgb_image(
                destData,
                r_channel.data(), g_channel.data(), b_channel.data(),
                width, height,
                rowBytes,
                true);
            break;
        }
        case bmdFormat8BitARGB: {
            pack_8bpc_rgb_image(
                destData,
                r_channel.data(), g_channel.data(), b_channel.data(),
                width, height,
                rowBytes,
                false);
            break;
        }
        case bmdFormat10BitRGB: {
            pack_10bpc_rgb_image(
                destData,
                r_channel.data(), g_channel.data(), b_channel.data(),
                width, height,
                rowBytes);
            break;
        }
        case bmdFormat8BitYUV: {
            pack_10bpc_yuv_image(
                destData,
                r_channel.data(), g_channel.data(), b_channel.data(),
                width, height,
                rowBytes);
            break;
        }
        case bmdFormat12BitRGB: {
            pack_12bpc_rgb_image(
                destData,
                r_channel.data(), g_channel.data(), b_channel.data(),
                width, height,
                rowBytes);
            break;
        }
        default:
            std::cerr << "[DeckLink] Unsupported pixel format: 0x" << std::hex << pixelFormat << std::dec << std::endl;
            return -8;
    }
    return 0;
 }