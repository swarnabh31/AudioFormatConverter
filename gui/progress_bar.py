"""Progress display widget — overall batch progress + per-file mini bars."""

from typing import Callable, List  # noqa: F401

import flet as ft  # noqa: D100

from core.conversion_models import ConversionJob
from gui.theme import ACCENT_SUBTITLE, ACCENT_TEXT, DARK_SURFACE


def create_progress_bar(jobs: List[ConversionJob]) -> ft.Column:
    """Build an overall progress bar and per-file mini progress bars.

    The *overall* bar reflects the weighted average of all job ``progress_pct`` values
    (queued jobs count as 0 %).  Per-file strips appear beneath it, one per queued file.

    Args:
        jobs: Live list of :class:`ConversionJob` objects.

    Returns:
        A populated :class:`ft.Column` ready for insertion into the UI layout.
    """
    overall_bar = ft.ProgressBar(
        value=0.0,
        color="white",
        bgcolor="#333344",
        border_radius=8,
        width=600,
    )

    overall_label = ft.Text("Overall: 0%", size=12, color=ACCENT_SUBTITLE)

    per_file_controls: List[ft.Control] = []

    col = ft.Column(
        controls=[
            overall_bar,
            overall_label,
        ] + per_file_controls,
        spacing=6,
    )

    return col


def refresh_progress_bar(
    overall_bar: ft.ProgressBar,
    overall_label: ft.Text,
    per_file_controls: List[ft.Control],
    jobs: List[ConversionJob],
    on_update: Callable[[], None],
) -> None:
    """Update progress bars in-place from the current state of *jobs*.

    Args:
        overall_bar: The main :class:`ft.ProgressBar` widget.
        overall_label: The label :class:`ft.Text` showing percentage text.
        per_file_controls: Mutable list of per-file mini progress bar widgets.
        jobs: Current :class:`ConversionJob` list.
        on_update: Callback to trigger a UI refresh after mutating controls.
    """
    if not jobs:
        overall_bar.value = 0.0
        overall_label.value = "Overall: 0%"
        per_file_controls.clear()
        on_update()
        return

    total_pct = sum(j.progress_pct for j in jobs) / len(jobs)
    overall_bar.value = max(0.0, min(1.0, total_pct / 100.0))
    overall_label.value = f"Overall: {total_pct:.1f}%"

    # Per-file bars — rebuild to keep list in sync with jobs list
    while len(per_file_controls) > len(jobs):
        per_file_controls.pop()
    while len(per_file_controls) < len(jobs):
        mini = ft.ProgressBar(
            value=0.0,
            color=ACCENT_PRIMARY,
            bgcolor="#333344",
            border_radius=4,
            width=200,
        )
        name_label = ft.Text("", size=10, color=ACCENT_SUBTITLE)
        mini_row = ft.Row([name_label, mini], spacing=8, alignment=ft.MainAxisAlignment.START)
        per_file_controls.append(mini_row)

    for idx, job in enumerate(jobs):
        row_widget = per_file_controls[idx]  # type: ignore[index]
        controls_list = row_widget.controls  # type: ignore[union-attr]
        if len(controls_list) >= 2:
            name_text = controls_list[0]
            mini_bar = controls_list[1]
            if isinstance(name_text, ft.Text):
                name_text.value = job.source_path.name
                name_text.update()
            if isinstance(mini_bar, ft.ProgressBar):
                mini_bar.value = max(0.0, min(1.0, job.progress_pct / 100.0))
                mini_bar.update()

    on_update()
