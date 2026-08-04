"""
Tests for the DeckLinkOutput protocol and the pydecklink-backed adapter.

Covers §spec:decklink-backend: the device layer is pydecklink, exposed
through a ``DeckLinkOutput`` protocol that both ``BMDDeckLink`` (hardware)
and ``MockBMDDeckLink`` (no hardware) satisfy. Hardware tests skip when no
DeckLink device is connected.
"""

import numpy as np
import pytest

import bmd_sg.decklink.bmd_decklink as bmd_decklink_module
from bmd_sg.decklink.bmd_decklink import (
    BMDDeckLink,
    DeckLinkOutput,
    HDRMetadata,
    PixelFormatType,
    get_decklink_devices,
)
from bmd_sg.decklink.mock import MockBMDDeckLink


def _hardware_available() -> bool:
    """Check whether at least one DeckLink device is connected."""
    try:
        return len(get_decklink_devices()) > 0
    except Exception:
        return False


requires_hardware = pytest.mark.skipif(
    not _hardware_available(), reason="No DeckLink device connected"
)


class TestBackend:
    """The device layer is pydecklink, not the private ctypes wrapper."""

    def test_module_does_not_load_ctypes_library(self) -> None:
        """No ctypes CDLL handle: libdecklink.dylib is not part of the backend."""
        assert not hasattr(bmd_decklink_module, "DecklinkSDKWrapper")

    def test_module_uses_pydecklink(self) -> None:
        """The adapter module imports pydecklink."""
        assert hasattr(bmd_decklink_module, "pydecklink")

    def test_get_decklink_devices_returns_names(self) -> None:
        """Device enumeration returns a list of device name strings."""
        devices = get_decklink_devices()
        assert isinstance(devices, list)
        assert all(isinstance(name, str) for name in devices)


class TestProtocolConformance:
    """Both device implementations satisfy DeckLinkOutput."""

    def test_mock_satisfies_protocol(self) -> None:
        device = MockBMDDeckLink(device_index=0)
        try:
            assert isinstance(device, DeckLinkOutput)
        finally:
            device.close()

    @requires_hardware
    def test_hardware_satisfies_protocol(self) -> None:
        with BMDDeckLink(device_index=0) as device:
            assert isinstance(device, DeckLinkOutput)


class TestHDRMetadataStructure:
    """HDRMetadata keeps its established constructor and attributes."""

    def test_defaults(self) -> None:
        metadata = HDRMetadata()
        assert metadata.maxCLL == 1000.0
        assert metadata.maxFALL == 50.0
        assert metadata.maxDisplayMasteringLuminance == 1000.0
        # Rec.2020 primaries are the default
        assert metadata.referencePrimaries.RedX == pytest.approx(0.708)
        assert metadata.referencePrimaries.WhiteX == pytest.approx(0.3127)

    def test_custom_values(self) -> None:
        from bmd_sg.decklink.bmd_decklink import EOTFType

        metadata = HDRMetadata(eotf=EOTFType.PQ, max_cll=10000.0, max_fall=400.0)
        assert metadata.EOTF == EOTFType.PQ.int_value
        assert metadata.maxCLL == 10000.0
        assert metadata.maxFALL == 400.0


@requires_hardware
class TestHardwareAdapter:
    """Adapter behavior against a connected DeckLink device."""

    def test_open_close_lifecycle(self) -> None:
        device = BMDDeckLink(device_index=0)
        assert device.is_open
        device.close()
        assert not device.is_open
        device.close()  # idempotent

    def test_invalid_index_raises(self) -> None:
        with pytest.raises(RuntimeError):
            BMDDeckLink(device_index=99)

    def test_supported_pixel_formats(self) -> None:
        with BMDDeckLink(device_index=0) as device:
            formats = device.get_supported_pixel_formats()
            assert len(formats) > 0
            assert all(isinstance(f, PixelFormatType) for f in formats)

    def test_pixel_format_roundtrip(self) -> None:
        with BMDDeckLink(device_index=0) as device:
            formats = device.get_supported_pixel_formats()
            target = formats[0]
            device.pixel_format = target
            assert device.pixel_format == target

    def test_supports_hdr_is_bool(self) -> None:
        with BMDDeckLink(device_index=0) as device:
            assert isinstance(device.supports_hdr, bool)

    def test_display_frame_smoke(self) -> None:
        """Full output path: HDR metadata + gray frame, synchronous display."""
        with BMDDeckLink(device_index=0) as device:
            formats = device.get_supported_pixel_formats()
            twelve_bit = [f for f in formats if f.bit_depth == 12]
            target = twelve_bit[0] if twelve_bit else formats[0]
            device.pixel_format = target

            if device.supports_hdr:
                device.set_hdr_metadata(HDRMetadata(max_cll=10000.0))

            device.start_playback()
            max_code = (1 << target.bit_depth) - 1
            frame = np.full((1080, 1920, 3), max_code // 2, dtype=np.uint16)
            device.display_frame(frame)
            device.stop_playback()
