"""Conversion settings panel widget — bitrate, sample rate, channel mode."""

from typing import Callable  # noqa: F401

import flet as ft  # noqa: D100

from core.conversion_models import ConversionSettings
from gui.theme import ACCENT_PRIMARY, ACCENT_SUBTITLE, ACCENT_TEXT, DARK_SURFACE, FONT_FAMILY


BITRATE_OPTIONS: list = [64, 128, 192, 256, 320]
SAMPLE_RATE_OPTIONS: list = [44100, 48000]


def create_settings_panel(
    current_settings: ConversionSettings,
    on_settings_changed: Callable[[ConversionSettings], None],
) -> ft.Column:
    """Build the conversion-settings :class:`ft.Column` with live-bound controls.

    All three controls (bitrate, sample rate, channel mode) emit ``on_settings_changed``
    immediately whenever their value changes — no "Apply" button is needed.

    Args:
        current_settings: Initial :class:`ConversionSettings` dictating defaults.
        on_settings_changed: Callback invoked with a fresh :class:`ConversionSettings`
            after any control change.

    Returns:
        A populated :class:`ft.Column` ready for insertion into the UI layout.
    """
    bitrate_dropdown = ft.Dropdown(
        label="Bitrate (kbps)",
        value=str(current_settings.bitrate),
        options=[ft.dropdown.Option(str(b)) for b in BITRATE_OPTIONS],
        width=200,
        bgcolor=DARK_SURFACE,
        color=ACCENT_TEXT,
    )

    sr_dropdown = ft.Dropdown(
        label="Sample Rate (Hz)",
        value=str(current_settings.sample_rate),
        options=[ft.dropdown.Option(str(sr)) for sr in SAMPLE_RATE_OPTIONS],
        width=200,
        bgcolor=DARK_SURFACE,
        color=ACCENT_TEXT,
    )

    mono_rb = ft.RadioGroup(
        content=ft.Row([
            ft.RadioButton(value="mono", content=ft.Text("Mono", size=12)),
            ft.RadioButton(value="stereo", content=ft.Text("Stereo", size=12)),
        ], spacing=16),
        value=current_settings.channel_mode,
    )

    def _emit() -> None:
        settings = ConversionSettings(
            bitrate=int(bitrate_dropdown.value),
            sample_rate=int(sr_dropdown.value),
            channel_mode=mono_rb.content.controls[0].value if mono_rb.content else "stereo",
        )
        # Ensure we pick the correct radio value
        for rb in (mono_rb.content.controls if mono_rb.content else []):  # type: ignore[attr-defined]
            if rb.selected:  # type: ignore[attr-defined]
                settings.channel_mode = rb.value  # type: ignore[attr-defined]
                break
        on_settings_changed(settings)

    bitrate_dropdown.on_change = lambda _: _emit()
    sr_dropdown.on_change = lambda _: _emit()
    mono_rb.on_change = lambda _: _emit()

    panel = ft.Column(
        controls=[
            ft.Text("Conversion Settings", size=16, weight="bold", color=ACCENT_TEXT),
            bitrate_dropdown,
            sr_dropdown,
            ft.Divider(height=1, thickness=1, color=ACCENT_SUBTITLE),
            ft.Text("Channel Mode:", size=12, color=ACCENT_TEXT),
            mono_rb,
        ],
        spacing=14,
    )

    return panel
