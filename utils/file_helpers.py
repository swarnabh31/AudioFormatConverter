"""File validation helpers — extension, magic-byte signatures, and size checks."""

import struct  # noqa: D100
from pathlib import Path  # noqa: I001
from typing import Optional, Dict, Any, Set  # noqa: F401


ALLOWED_EXTENSIONS: frozenset = frozenset({".wav", ".flac", ".m4a", ".ogg"})

# Magic-byte signatures (offset -> expected bytes)
MAGIC_SIGNATURES: Dict[str, tuple] = {
    ".wav": ((0, b"RIFF"), (8, b"WAV")),
    ".flac": ((0, b"fLaC"),),
    ".m4a": ((4, b"ftyp"),),  # ftyp box at offset 4 inside ftyp/ISO media layout
    ".ogg": ((0, b"OggS"),),
}


def validate_file(path: Path) -> Dict[str, Any]:
    """Validate a single file for acceptance into the converter queue.

    Checks three layers:
      1. Extension membership in :data:`ALLOWED_EXTENSIONS`.
      2. Magic-byte (file signature) match against :data:`MAGIC_SIGNATURES`.
      3. File size does not exceed 2 GB (returns a ``warning`` key when exceeded).

    Args:
        path: Resolved :class:`Path` to the candidate file.

    Returns:
        A dict with keys:
            ``"valid"`` (bool) — always present; ``True`` means the file is accepted.
            ``"format"`` (str) — detected extension lowercased, e.g. ``"wav"``.
            ``"size_bytes"`` (int) — file size.
            ``"warning"`` (Optional[str]) — non-fatal warning text if any.

    Raises:
        OSError: If the file cannot be read at all (e.g. permission denied).
    """
    ext: str = path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return {"valid": False, "format": ext, "size_bytes": 0, "warning": None}

    size: int = path.stat().st_size
    warning: Optional[str] = None
    if size > 2 * 1024 ** 3:
        warning = f"File is {human_size(size)} — very large files may use significant memory during metadata reading."

    # Magic-byte check
    try:
        with open(str(path), "rb") as fh:
            for (offset, expected) in MAGIC_SIGNATURES.get(ext, ()):
                fh.seek(offset)
                header = fh.read(len(expected))
                if header != expected:
                    return {"valid": False, "format": ext, "size_bytes": size, "warning": None}
    except (OSError, IOError):
        return {"valid": False, "format": ext, "size_bytes": 0, "warning": None}

    return {"valid": True, "format": ext, "size_bytes": size, "warning": warning}


def human_size(size_bytes: int) -> str:
    """Convert a byte count to a human-readable string (e.g. ``'4.2 MB'``).

    Args:
        size_bytes: Non-negative integer byte count.

    Returns:
        Formatted string like ``"0 B"``, ``"1.5 KB"``, ``"3.7 MB"``, or ``"8.1 GB"``.
    """
    if size_bytes < 0:
        raise ValueError("size_bytes must be non-negative")

    units = ["B", "KB", "MB", "GB"]
    idx = 0
    val = float(size_bytes)
    while val >= 1024 and idx < len(units) - 1:
        val /= 1024
        idx += 1

    if idx == 0:
        return f"{int(val)} B"
    return f"{val:.1f} {units[idx]}"


def get_supported_extensions() -> Set[str]:
    """Return the set of file extensions this converter accepts.

    Returns:
        A ``frozenset`` of lowercase extension strings including their leading dot.
    """
    return ALLOWED_EXTENSIONS.copy()
