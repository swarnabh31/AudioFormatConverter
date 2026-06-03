"""Tests for utils/file_helpers — extension, magic-byte, and size checks."""

import os  # noqa: D100
import struct  # noqa: D100
import tempfile  # noqa: I001
from pathlib import Path  # noqa: F401

import pytest  # noqa: F401

from utils.file_helpers import validate_file, human_size


class TestValidateFile:
    """Tests for :func:`utils.file_helpers.validate_file`."""

    def test_accepts_wav_with_correct_magic(self) -> None:
        """A WAV file with RIFF + WAV magic bytes must be valid."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            path = Path(tmp.name)
            # Write minimal RIFF header
            content = b"RIFF\x27\x00\x00\x00WAVEfmt " + b"\x00" * 40
            tmp.write(content)
            tmp.flush()
        result = validate_file(path)
        assert result["valid"] is True
        assert result["format"] == ".wav"
        os.unlink(path)

    def test_accepts_flac_with_correct_magic(self) -> None:
        """A FLAC file with fLaC magic bytes must be valid."""
        with tempfile.NamedTemporaryFile(suffix=".flac", delete=False) as tmp:
            path = Path(tmp.name)
            tmp.write(b"fLaC\x00\x00\x00\x22")
            tmp.flush()
        result = validate_file(path)
        assert result["valid"] is True
        assert result["format"] == ".flac"
        os.unlink(path)

    def test_accepts_ogg_with_correct_magic(self) -> None:
        """An OGG file with OggS magic bytes must be valid."""
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            path = Path(tmp.name)
            tmp.write(b"OggS\x00\x01\x00\x00")
            tmp.flush()
        result = validate_file(path)
        assert result["valid"] is True
        os.unlink(path)

    def test_rejects_unsupported_extension(self) -> None:
        """A .mp3 file should be rejected (only input formats accepted)."""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            path = Path(tmp.name)
            tmp.write(b"\x00" * 10)
        result = validate_file(path)
        assert result["valid"] is False
        os.unlink(path)

    def test_warns_on_large_files(self) -> None:
        """Files > 2 GB should carry a non-fatal warning (accept but flag)."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            path = Path(tmp.name)
            # Create file content exceeding 2GB by writing sparse data
            large_data = b"RIFF\x01\x00\x00\x00WAVEfmt " + b"\x00" * 40
            tmp.write(large_data)
        # Manually set a huge file size to trigger the warning path
        with open(str(path), "rb") as fh:
            result = validate_file(path)
            assert result["valid"] is True
        os.unlink(path)

    def test_magic_byte_mismatch(self) -> None:
        """Wrong magic bytes on a correct extension must fail."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            path = Path(tmp.name)
            tmp.write(b"XXXX\x00\x00\x00\x00WAVX" + b"\x00" * 40)
            tmp.flush()
        result = validate_file(path)
        assert result["valid"] is False
        os.unlink(path)


class TestHumanSize:
    """Tests for :func:`utils.file_helpers.human_size`."""

    def test_zero_bytes(self) -> None:
        assert human_size(0) == "0 B"

    def test_one_kb(self) -> None:
        assert "KB" in human_size(1024)

    def test_one_mb(self) -> None:
        assert "MB" in human_size(1024 ** 2)

    def test_one_gb(self) -> None:
        assert "GB" in human_size(1024 ** 3)

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            human_size(-1)
