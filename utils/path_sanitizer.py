"""Path traversal prevention and output path construction utilities."""

import os  # noqa: D100
import pathlib  # noqa: I001
from pathlib import Path  # noqa: F401
from typing import Tuple  # noqa: F401


def sanitize_input_path(user_path: str) -> Tuple[bool, str]:
    """Validate and canonicalize a user-supplied file path.

    Checks performed:
      1. Path exists as a regular file (not directory).
      2. Resolved path has length <= 255 characters.
      3. Base filename does not start with ``-`` (prevents FFmpeg flag injection).
      4. No embedded null bytes anywhere in the string.

    Args:
        user_path: The raw path string supplied by the user (e.g. from drag-drop).

    Returns:
        A ``(ok, resolved_or_error)`` tuple.
        *ok* is ``True`` and the second element is the canonical ``Path(str)`` when
        validation passes; otherwise *ok* is ``False`` and the second element is an
        error message string.
    """
    # Check for null bytes anywhere in the string first (cheap).
    if "\x00" in user_path:
        return (False, "Path contains a null byte")

    try:
        p = Path(user_path)
        if not p.is_file():
            return (False, f"File does not exist or is not a regular file: {user_path}")
        resolved = p.resolve()
        resolved_str = str(resolved)
        if len(resolved_str) > 255:
            return (False, "Resolved path exceeds maximum allowed length of 255 characters")
        basename = resolved.name
        if basename.startswith("-"):
            return (False, f"Filename must not start with '-' to prevent FFmpeg flag injection: {basename}")
        return (True, str(resolved))

    except (OSError, ValueError) as exc:
        return (False, str(exc))


def sanitize_output_path(source_path: Path, output_folder: str = "") -> Tuple[bool, str, str]:
    """Construct and validate the output MP3 path for a given source file.

    The output filename follows the pattern ``<source_stem>_converted.mp3``.

    Args:
        source_path: Canonical :class:`Path` to the original audio file.
        output_folder: Optional directory in which to place the output; defaults to
            the source file's own parent directory.

    Returns:
        A ``(ok, error_msg_or_empty, resolved_output_str)`` tuple.
    """
    if "\x00" in str(output_folder):
        return (False, "Output folder path contains a null byte", "")

    stem: str = source_path.stem
    out_name: str = f"{stem}_converted.mp3"

    target_dir: Path = Path(output_folder) if output_folder else source_path.parent
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return (False, f"Cannot create output directory: {target_dir}", "")

    out_path: Path = (target_dir / out_name).resolve()
    resolved_str: str = str(out_path)

    if len(resolved_str) > 255:
        return (False, "Output path exceeds maximum allowed length of 255 characters", "")

    return (True, "", resolved_str)


def ensure_parent_dirs(path: Path) -> bool:
    """Create parent directories for *path* if they do not exist.

    Args:
        path: Target file path whose parents should be created.

    Returns:
        ``True`` if creation succeeded; ``False`` on any OSError.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        return True
    except OSError:
        return False
