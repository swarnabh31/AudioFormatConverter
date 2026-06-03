"""Application settings loader — reads config/settings.json with fallback defaults."""

import json  # noqa: D100
import os  # noqa: D100
from pathlib import Path  # noqa: I001
from typing import Any, Dict  # noqa: F401


_DEFAULT_SETTINGS: Dict[str, Any] = {
    "default_bitrate": 192,
    "default_sample_rate": 44100,
    "default_channel_mode": "stereo",
    "output_folder": None,
    "max_concurrency": 1,
    "compact_mode": False,
    "last_opened_directory": None,
}


def _settings_file_path() -> Path:
    """Return the path to ``config/settings.json`` relative to this module's parent."""
    return Path(__file__).resolve().parent.parent / "config" / "settings.json"


def load_settings() -> Dict[str, Any]:
    """Load application settings from ``config/settings.json``.

    If the file does not exist or is invalid JSON, returns a fresh dict populated
    with :data:`_DEFAULT_SETTINGS`.

    Returns:
        A ``dict`` with all expected keys guaranteed to be present (defaults filled in).
    """
    settings_path = _settings_file_path()
    try:
        if settings_path.exists():
            with open(str(settings_path), "r", encoding="utf-8") as fh:
                loaded = json.load(fh)
                if isinstance(loaded, dict):
                    merged = {**_DEFAULT_SETTINGS, **loaded}
                    return merged
    except (json.JSONDecodeError, OSError):
        pass

    return _DEFAULT_SETTINGS.copy()


def save_settings(settings: Dict[str, Any]) -> bool:
    """Persist *settings* dict to ``config/settings.json``.

    Args:
        settings: A dict matching the :data:`_DEFAULT_SETTINGS` schema.

    Returns:
        ``True`` on successful write; ``False`` on any I/O error.
    """
    settings_path = _settings_file_path()
    try:
        with open(str(settings_path), "w", encoding="utf-8") as fh:
            json.dump(settings, fh, indent=4)
        return True
    except OSError:
        return False
