#!/usr/bin/env python3
"""
API Four Pattern Demo - HTTP API Example

Displays four different test patterns in sequence using the BMD Signal Generator
REST API. This demonstrates real-time pattern updates via HTTP requests to the
/update_color endpoint.

Prerequisites:
1. Start the API server first: bmd-cli api-server
2. Ensure device is connected and configured properly
3. Run this script: python examples/api_pattern_demo.py
"""

import sys
import time

try:
    import requests
except ImportError:
    print("❌ Error: requests library not found")
    print("💡 Install with: pip install requests")
    sys.exit(1)

# API configuration
API_BASE_URL = "http://localhost:8000"
UPDATE_COLOR_ENDPOINT = f"{API_BASE_URL}/update_color"
STATUS_ENDPOINT = f"{API_BASE_URL}/status"


def check_api_server():
    """Check if API server is running and device is initialized."""
    try:
        response = requests.get(STATUS_ENDPOINT, timeout=2)
        response.raise_for_status()
        status = response.json()

        if not status.get("device_connected", False):
            print("❌ Error: Device not connected")
            print(
                "💡 Make sure DeckLink device is connected and start API "
                "server with: bmd-cli api-server"
            )
            return False

        print(f"✅ Connected to {status.get('device_name', 'Unknown Device')}")
        resolution = status.get("resolution", {"width": 0, "height": 0})
        print(f"📐 Resolution: {resolution['width']}x{resolution['height']}")
        print(f"🎨 Pixel format: {status.get('pixel_format', 'Unknown')}")
        return True

    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to API server")
        print("💡 Start the API server first: bmd-cli api-server")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error checking API status: {e}")
        return False


def update_pattern(colors: list[list[int]], pattern_name: str) -> bool:
    """Update pattern via API and handle errors."""
    try:
        payload = {"colors": colors}
        response = requests.post(UPDATE_COLOR_ENDPOINT, json=payload, timeout=5)
        response.raise_for_status()

        result = response.json()
        if result.get("success", False):
            message = result.get("message", "Updated successfully")
            print(f"✅ {pattern_name}: {message}")
            return True
        else:
            message = result.get("message", "Update failed")
            print(f"❌ {pattern_name}: {message}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ {pattern_name}: API request failed - {e}")
        return False


def main():
    """Run the four pattern demo sequence."""
    print("🎨 BMD Signal Generator API Pattern Demo")
    print("=" * 50)

    # Check if API server is available
    if not check_api_server():
        sys.exit(1)

    print("\n🚀 Starting pattern sequence...\n")

    # Pattern 1: Red/Black/Green/Black checkerboard
    print("Pattern 1: Red/Black/Green/Black Checkerboard")
    colors_1 = [
        [2000, 0, 0],  # Red
        [0, 0, 0],  # Black
        [0, 2000, 0],  # Green
        [0, 0, 0],  # Black
    ]
    if update_pattern(colors_1, "Red/Black/Green/Black"):
        time.sleep(3)

    # Pattern 2: Solid white (100 nits)
    print("Pattern 2: Solid White (100 nits)")
    white_100nits = [[2081, 2081, 2081]]
    if update_pattern(white_100nits, "Solid White"):
        time.sleep(3)

    # Pattern 3: Color bars (Cyan/Magenta/Yellow/Black)
    print("Pattern 3: Color Bars")
    colors_3 = [
        [0, 3276, 3276],  # Cyan
        [3276, 0, 3276],  # Magenta
        [3276, 3276, 0],  # Yellow
        [0, 0, 0],  # Black
    ]
    if update_pattern(colors_3, "Color Bars"):
        time.sleep(3)

    # Pattern 4: High contrast black/white checkerboard
    print("Pattern 4: High Contrast Black/White")
    colors_4 = [
        [4095, 4095, 4095],  # Pure white
        [0, 0, 0],  # Pure black
    ]
    if update_pattern(colors_4, "High Contrast"):
        time.sleep(3)

    print("\n✅ Demo complete!")
    print("💡 API server is still running - use Ctrl+C to stop it")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
