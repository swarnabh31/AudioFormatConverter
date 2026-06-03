"""FFmpeg detection and validation utilities.

Module-level, stateless functions that locate FFmpeg on PATH and verify its version.
"""

import subprocess  # noqa: D100
from pathlib import Path  # noqa: I001
from typing import Optional, Tuple  # noqa: F401


def detect_ffmpeg() -> Optional[str]:
    """Return the absolute path to the ffmpeg binary if it exists on PATH.

    Uses ``shutil.which``-like logic via :func:`subprocess.run` with ``capture_output=True``
    and a short timeout so detection never hangs the UI thread.

    Returns:
        Absolute path string to ``ffmpeg.exe`` (or ``ffmpeg``) if found; ``None`` otherwise.
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        if result.returncode == 0:
            ffmpeg_path: Optional[str] = subprocess.check_output(
                ["where", "ffmpeg"], encoding="utf-8", timeout=3
            ).strip() or None
            if ffmpeg_path is not None and Path(ffmpeg_path).exists():
                return str(Path(ffmpeg_path).resolve())
            # Fallback: just confirm the binary runs; use generic path
            return "ffmpeg"
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def validate_version(path: str) -> Tuple[bool, str]:
    """Run ``ffprobe -version`` and parse the major.minor.patch version.

    Args:
        path: Path string to an ffmpeg/ffprobe binary (e.g. ``"ffmpeg"`` or full path).

    Returns:
        A ``(is_valid, version_string)`` tuple.  *is_valid* is ``True`` when the
        detected version is >= 4.0.0; *version_string* is the human-readable string
        (e.g. ``"5.1.2"``).
    """
    try:
        result = subprocess.run(
            [path, "-version"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        if result.returncode != 0:
            return (False, "Unable to read version")

        # ffmpeg -version output starts with "ffmpeg version X.Y.Z ..."
        first_line = result.stdout.splitlines()[0].strip()
        import re

        match = re.search(r"version\s+(\d+)\.(\d+)\.(\d+)", first_line)
        if not match:
            return (False, "Unable to parse version string")

        major, minor, patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
        version_str = f"{major}.{minor}.{patch}"

        # Require >= 4.0.0
        if major < 4 or (major == 4 and minor < 0):
            return (False, f"FFmpeg {version_str} found; minimum required is 4.0.0")

        return (True, version_str)

    except subprocess.TimeoutExpired:
        return (False, "Version check timed out")
    except Exception as exc:
        return (False, str(exc))
