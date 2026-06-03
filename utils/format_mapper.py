"""Input format to FFmpeg codec-name mapping.

Every input format supported by the converter maps to the corresponding
FFmpeg decoder / input format name.  This module also provides reverse look-ups
and a constant list of accepted formats.
"""

from typing import Dict  # noqa: F401

# Mapping from lowercased file extension (with leading dot) → FFmpeg codec / format name.
INPUT_FORMAT_MAP: Dict[str, str] = {
    ".wav": "wav",
    ".flac": "flac",
    ".m4a": "mp4",
    ".ogg": "ogg",
}

# Reverse lookup: codec name → extension (used for display / logging).
REVERSE_FORMAT_MAP: Dict[str, str] = {v: k for k, v in INPUT_FORMAT_MAP.items()}


def get_ffmpeg_input_format(extension: str) -> str:
    """Return the FFmpeg input format name for the given file extension.

    Args:
        extension: Lowercase extension including leading dot (e.g. ``".wav"``).

    Returns:
        The FFmpeg format string to use as ``-f <format>`` before ``-i <path>``.

    Raises:
        ValueError: If the extension is not in the known map.
    """
    ext: str = extension.lower()
    if ext not in INPUT_FORMAT_MAP:
        raise ValueError(f"Unsupported input format: {ext!r}. Supported: {sorted(INPUT_FORMAT_MAP)}")
    return INPUT_FORMAT_MAP[ext]


def get_output_extension(_input_format: str) -> str:
    """Return the output file extension for MP3 (the only supported output).

    Args:
        _input_format: The original input format string (unused — kept for API symmetry).

    Returns:
        ``".mp3"``.
    """
    return ".mp3"


def get_supported_formats() -> list[str]:
    """Return a list of supported input format names (e.g. ``["wav", "flac", ...]``).

    Returns:
        Alphabetically sorted list of FFmpeg input format strings.
    """
    return sorted(INPUT_FORMAT_MAP.values())
