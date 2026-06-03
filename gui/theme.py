"""Flet dark-theme colour constants and a theme-applier helper."""

import flet as ft  # noqa: D100


# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
DARK_BG: str = "#121218"            """Main page background."""
DARK_SURFACE: str = "#1E1E2E"       """Card / container surfaces."""
DARK_HOVER: str = "#2A2A3C"         """Hover highlight on interactive elements."""
ACCENT_PRIMARY: str = "#7C4DFF"     """Primary action (Convert All) button."""
ACCENT_PRIMARY_ON_HOVER: str = "#9572FF"
ACCENT_SUCCESS: str = "#00C853"     """'Done' status text / indicator."""
ACCENT_WARNING: str = "#FFB300"     """'Converting' status indicator."""
ACCENT_ERROR: str = "#FF1744"       """'Error' status indicator."""
ACCENT_TEXT: str = "#EAEAEA"        """Primary label text."""
ACCENT_SUBTITLE: str = "#9E9E9E"    """Secondary / muted text."""

FONT_FAMILY: str = "Roboto"
CORNER_RADIUS: int = 8
SHADOW_SPACING: int = 3


def apply_theme(page: ft.Page) -> None:
    """Apply the Sovereign dark theme to *page* and return a shared style dict.

    Args:
        page: Flet :class:`Page` instance being themed.

    Returns:
        A :class:`dict` containing commonly-used style keys for reuse across widgets.
    """
    page.bg_color = DARK_BG
    page.font_family = FONT_FAMILY
    page.theme_mode = ft.ThemeMode.DARK  # type: ignore[attr-defined]

    surface_text_style: ft.TextStyle = ft.TextStyle(
        color=ACCENT_TEXT,
        size=14,
        family=FONT_FAMILY,
    )

    title_text_style: ft.TextStyle = ft.TextStyle(
        color=ACCENT_PRIMARY,
        size=20,
        weight="bold",
        family=FONT_FAMILY,
    )

    subtitle_text_style: ft.TextStyle = ft.TextStyle(
        color=ACCENT_SUBTITLE,
        size=12,
        family=FONT_FAMILY,
    )

    surface_style: dict = {
        "bgcolor": DARK_SURFACE,
        "border_radius": CORNER_RADIUS,
        "padding": 20,
        "shadow": ft.BoxShadow(spacing=SHADOW_SPACING, color="#00000055"),
    }

    return {
        "surface_style": surface_style,
        "surface_text": surface_text_style,
        "title_text": title_text_style,
        "subtitle_text": subtitle_text_style,
    }
