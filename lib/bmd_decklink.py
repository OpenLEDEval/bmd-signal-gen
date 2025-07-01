#!/usr/bin/env python3
"""
Python wrapper for DeckLink signal generation using ctypes.
"""
import ctypes
import os
import sys
import numpy as np

# Load the DeckLink library
try:
    # Try to load from the lib directory relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    lib_path = os.path.join(script_dir, 'libdecklink.dylib')
    decklink = ctypes.CDLL(lib_path)
except OSError as e:
    print(f"Failed to load DeckLink library from {lib_path}: {e}")
    sys.exit(1)

# Define function signatures
decklink.decklink_get_device_count.argtypes = []
decklink.decklink_get_device_count.restype = ctypes.c_int

decklink.decklink_get_device_name_by_index.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
decklink.decklink_get_device_name_by_index.restype = ctypes.c_int

decklink.decklink_open_output_by_index.argtypes = [ctypes.c_int]
decklink.decklink_open_output_by_index.restype = ctypes.c_void_p

decklink.decklink_close.argtypes = [ctypes.c_void_p]
decklink.decklink_close.restype = None

decklink.decklink_start_output.argtypes = [ctypes.c_void_p]
decklink.decklink_start_output.restype = ctypes.c_int

decklink.decklink_stop_output.argtypes = [ctypes.c_void_p]
decklink.decklink_stop_output.restype = ctypes.c_int

decklink.decklink_get_supported_pixel_format_count.argtypes = [ctypes.c_void_p]
decklink.decklink_get_supported_pixel_format_count.restype = ctypes.c_int

decklink.decklink_get_supported_pixel_format_name.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
decklink.decklink_get_supported_pixel_format_name.restype = ctypes.c_int

# Add the new function signatures
if hasattr(decklink, 'decklink_set_pixel_format'):
    decklink.decklink_set_pixel_format.argtypes = [ctypes.c_void_p, ctypes.c_int]
    decklink.decklink_set_pixel_format.restype = ctypes.c_int

if hasattr(decklink, 'decklink_get_pixel_format'):
    decklink.decklink_get_pixel_format.argtypes = [ctypes.c_void_p]
    decklink.decklink_get_pixel_format.restype = ctypes.c_int

if hasattr(decklink, 'decklink_set_eotf_metadata'):
    decklink.decklink_set_eotf_metadata.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_uint16, ctypes.c_uint16]
    decklink.decklink_set_eotf_metadata.restype = ctypes.c_int

# Frame data management
if hasattr(decklink, 'decklink_set_frame_data'):
    decklink.decklink_set_frame_data.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint16), ctypes.c_int, ctypes.c_int]
    decklink.decklink_set_frame_data.restype = ctypes.c_int

# Frame management
if hasattr(decklink, 'decklink_create_frame_from_data'):
    decklink.decklink_create_frame_from_data.argtypes = [ctypes.c_void_p]
    decklink.decklink_create_frame_from_data.restype = ctypes.c_int

if hasattr(decklink, 'decklink_schedule_frame_for_output'):
    decklink.decklink_schedule_frame_for_output.argtypes = [ctypes.c_void_p]
    decklink.decklink_schedule_frame_for_output.restype = ctypes.c_int

if hasattr(decklink, 'decklink_start_scheduled_playback'):
    decklink.decklink_start_scheduled_playback.argtypes = [ctypes.c_void_p]
    decklink.decklink_start_scheduled_playback.restype = ctypes.c_int



# Version info
if hasattr(decklink, 'decklink_get_driver_version'):
    decklink.decklink_get_driver_version.argtypes = []
    decklink.decklink_get_driver_version.restype = ctypes.c_char_p

def get_decklink_driver_version():
    return decklink.decklink_get_driver_version().decode('utf-8')

if hasattr(decklink, 'decklink_get_sdk_version'):
    decklink.decklink_get_sdk_version.argtypes = []
    decklink.decklink_get_sdk_version.restype = ctypes.c_char_p

def get_decklink_sdk_version():
    return decklink.decklink_get_sdk_version().decode('utf-8')

class BMDDeckLink:
    """Minimal Python wrapper for DeckLink color patch output."""
    def __init__(self, device_index=0):
        self.handle = decklink.decklink_open_output_by_index(device_index)
        if not self.handle:
            raise RuntimeError(f"No DeckLink output device found at index {device_index}")
        self.started = False
    
    def close(self):
        """Close the device and free resources."""
        if self.handle:
            if self.started:
                decklink.decklink_stop_output(self.handle)
            decklink.decklink_close(self.handle)
            self.handle = None
    

    
    def start(self):
        """Start outputting the color patch."""
        if not self.handle:
            raise RuntimeError("Device not open")
        if self.started:
            return
        res = decklink.decklink_start_output(self.handle)
        if res != 0:
            raise RuntimeError(f"Failed to start output (error {res})")
        self.started = True
    
    def stop(self):
        """Stop output."""
        if not self.handle or not self.started:
            return
        decklink.decklink_stop_output(self.handle)
        self.started = False
    
    def get_supported_pixel_formats(self):
        """Get list of supported pixel format names."""
        if not self.handle:
            raise RuntimeError("Device not open")
        
        count = decklink.decklink_get_supported_pixel_format_count(self.handle)
        formats = []
        for i in range(count):
            name = ctypes.create_string_buffer(256)
            if decklink.decklink_get_supported_pixel_format_name(self.handle, i, name, 256) == 0:
                formats.append(name.value.decode('utf-8'))
        return formats
    
    def set_pixel_format(self, format_index):
        """Set the pixel format by index."""
        if not self.handle:
            raise RuntimeError("Device not open")
        res = decklink.decklink_set_pixel_format(self.handle, format_index)
        if res != 0:
            raise RuntimeError(f"Failed to set pixel format (error {res})")
    
    def get_pixel_format(self):
        """Get the current pixel format index."""
        if not self.handle:
            raise RuntimeError("Device not open")
        return decklink.decklink_get_pixel_format(self.handle)
    
    def set_frame_eotf(self, eotf=0, maxCLL=0, maxFALL=0):
        """Set EOTF metadata for all future frames."""
        if not self.handle:
            raise RuntimeError("Device not open")
        res = decklink.decklink_set_eotf_metadata(self.handle, eotf, maxCLL, maxFALL)
        if res != 0:
            raise RuntimeError(f"Failed to set EOTF metadata (error {res})")
    
    def set_frame_data(self, frame_data):
        """Set frame data from numpy array.
        
        Args:
            frame_data: numpy array with shape (height, width, channels) or (height, width)
        """
        if not self.handle:
            raise RuntimeError("Device not open")
        
        if not isinstance(frame_data, np.ndarray):
            raise ValueError("frame_data must be a numpy array")
        
        # Get dimensions
        if frame_data.ndim == 2:
            height, width = frame_data.shape
            channels = 1
        elif frame_data.ndim == 3:
            height, width, channels = frame_data.shape
        else:
            raise ValueError("frame_data must be 2D or 3D array")
        
        # Ensure data is uint16 and contiguous
        if frame_data.dtype != np.uint16:
            frame_data = frame_data.astype(np.uint16)
        frame_data = np.ascontiguousarray(frame_data)
        
        # Get pointer to data
        data_ptr = frame_data.ctypes.data_as(ctypes.POINTER(ctypes.c_uint16))
        res = decklink.decklink_set_frame_data(self.handle, data_ptr, width, height)
        if res != 0:
            raise RuntimeError(f"Failed to set frame data (error {res})")
    
    def create_frame(self):
        """Create a video frame from pending frame data."""
        if not self.handle:
            raise RuntimeError("Device not open")
        res = decklink.decklink_create_frame_from_data(self.handle)
        if res != 0:
            raise RuntimeError(f"Failed to create frame (error {res})")
    
    def schedule_frame(self):
        """Schedule the current frame for output."""
        if not self.handle:
            raise RuntimeError("Device not open")
        res = decklink.decklink_schedule_frame_for_output(self.handle)
        if res != 0:
            raise RuntimeError(f"Failed to schedule frame (error {res})")
    
    def start_playback(self):
        """Start scheduled playback."""
        if not self.handle:
            raise RuntimeError("Device not open")
        res = decklink.decklink_start_scheduled_playback(self.handle)
        if res != 0:
            raise RuntimeError(f"Failed to start playback (error {res})")
    

    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

def get_decklink_devices():
    """Get list of available DeckLink device names."""
    count = decklink.decklink_get_device_count()
    devices = []
    for i in range(count):
        name = ctypes.create_string_buffer(256)
        if decklink.decklink_get_device_name_by_index(i, name, 256) == 0:
            devices.append(name.value.decode('utf-8'))
    return devices