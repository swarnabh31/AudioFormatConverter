"""Tests for utils/format_mapper — extension-to-FFmpeg codec mapping."""

from utils.format_mapper import get_ffmpeg_input_format, get_output_extension, get_supported_formats, REVERSE_FORMAT_MAP


def test_get_ffmpeg_input_format_wav() -> None:
    assert get_ffmpeg_input_format(".wav") == "wav"


def test_get_ffmpeg_input_format_flac() -> None:
    assert get_ffmpeg_input_format(".flac") == "flac"


def test_get_ffmpeg_input_format_m4a() -> None:
    assert get_ffmpeg_input_format(".m4a") == "mp4"


def test_get_ffmpeg_input_format_ogg() -> None:
    assert get_ffmpeg_input_format(".ogg") == "ogg"


def test_get_ffmpeg_input_format_uppercase() -> None:
    assert get_ffmpeg_input_format(".WAV") == "wav"


def test_get_ffmpeg_input_format_rejects_invalid() -> None:
    from utils.format_mapper import INPUT_FORMAT_MAP
    for ext in [".mp3", ".ape", ".wma"]:
        try:
            get_ffmpeg_input_format(ext)
        except ValueError:
            pass  # expected
        else:
            assert False, f"Expected ValueError for {ext}"


def test_get_output_extension() -> None:
    assert get_output_extension("wav") == ".mp3"
    assert get_output_extension("flac") == ".mp3"


def test_get_supported_formats() -> None:
    formats = get_supported_formats()
    assert isinstance(formats, list)
    assert len(formats) == 4
    assert "flac" in formats
    assert "mp4" in formats
    assert "ogg" in formats
    assert "wav" in formats


def test_reverse_format_map_coverage() -> None:
    for codec_name, ext in REVERSE_FORMAT_MAP.items():
        assert get_ffmpeg_input_format(ext) == codec_name
