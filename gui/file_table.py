"""Real-time file status table widget for queued conversions."""

from typing import Callable, List  # noqa: F401

import flet as ft  # noqa: D100

from core.conversion_models import ConversionJob, JobStatus
from gui.theme import ACCENT_SUBTITLE, ACCENT_TEXT, DARK_SURFACE, FONT_FAMILY
from utils.file_helpers import human_size


def create_file_table(
    jobs: List[ConversionJob],
    on_update: Callable[[], None],
) -> ft.Table:
    """Build a :class:`ft.Table` that displays every queued conversion job.

    Columns: Filename | Format | Size | Progress | Status.
    Each cell is individually addressable so the converter engine can update progress
    and status in-place without rebuilding the whole table.

    Args:
        jobs: The live list of :class:`ConversionJob` objects managed by the queue.
        on_update: Callback triggered after each row-cell update to force a page refresh.

    Returns:
        A populated :class:`ft.Table` widget ready for insertion into the UI layout.
    """
    table = ft.Table(
        border=ft.border.all(1, ACCENT_SUBTITLE),
        border_radius=8,
        horizontal_margin=4,
    )

    header_row = ftTableRow(
        cells=[
            "Filename",
            "Format",
            "Size",
            "Progress",
            "Status",
        ],
        bold=True,
    )
    table.columns = header_row.cells  # type: ignore[assignment]
    table.rows.append(header_row)

    return table


class _JobRowBuilder:
    """Helper that builds a single row from a :class:`ConversionJob`."""

    def __init__(self, job: ConversionJob, on_update: Callable[[], None]) -> None:
        self.job = job
        self.on_update = on_update
        self.cells: List[ft.Control] = []
        self._build()

    def _truncated_filename(self) -> str:
        """Return the basename with ellipsis truncation for long names."""
        name = self.job.source_path.name
        if len(name) > 25:
            return name[:22] + "..."
        return name

    def _status_icon(self) -> str:
        """Map JobStatus → unicode emoji string."""
        status_map = {
            JobStatus.QUEUED: "⏳",
            JobStatus.CONVERTING: "🔄",
            JobStatus.DONE: "✅",
            JobStatus.ERROR: "❌",
        }
        return status_map.get(self.job.status, "⏳")

    def _status_color(self) -> str:
        """Map JobStatus → Flet text color."""
        from gui import theme as t
        color_map = {
            JobStatus.QUEUED: ACCENT_SUBTITLE,
            JobStatus.CONVERTING: t.ACCENT_WARNING,
            JobStatus.DONE: t.ACCENT_SUCCESS,
            JobStatus.ERROR: t.ACCENT_ERROR,
        }
        return color_map.get(self.job.status, ACCENT_TEXT)

    def _progress_bar(self) -> ft.ProgressBar:
        """Inline progress bar for the row (width 80 px)."""
        return ft.ProgressBar(
            value=self.job.progress_pct / 100.0 if self.job.progress_pct else 0,
            width=90,
            color="white",
            bgcolor="#333344",
            border_radius=4,
        )

    def _build(self) -> None:
        """Populate ``self.cells`` from the job's current state."""
        filename_cell = ft.Text(
            self._truncated_filename(),
            color=ACCENT_TEXT,
            size=12,
            font_family=FONT_FAMILY,
        )

        format_cell = ft.Text(
            self.job.original_format.upper(),
            color=ACCENT_SUBTITLE,
            size=12,
            font_family=FONT_FAMILY,
        )

        size_cell = ft.Text(
            human_size(self.job.original_size_bytes),
            color=ACCENT_SUBTITLE,
            size=12,
            font_family=FONT_FAMILY,
        )

        progress_bar = self._progress_bar()

        status_text = ft.Text(
            f"{self._status_icon()} {self.job.status.value}",
            color=self._status_color(),
            size=12,
            font_family=FONT_FAMILY,
        )

        self.cells = [filename_cell, format_cell, size_cell, progress_bar, status_text]


def ftTableRow(cells: List[str], bold: bool = False) -> ft.TableRow:
    """Convenience helper to build a :class:`ft.TableRow` from label strings."""
    style = ft.TextStyle(weight="bold" if bold else "normal", color=ACCENT_TEXT, size=12, font_family=FONT_FAMILY)
    return ft.TableRow(
        cells=[ft.Text(label, style=style) for label in cells]  # type: ignore[arg-type]
    )


def refresh_file_table(table: ft.Table, jobs: List[ConversionJob], on_update: Callable[[], None]) -> None:
    """Rebuild the data rows of *table* from the current state of *jobs*.

    Preserves the header row (first row) and replaces all subsequent rows.

    Args:
        table: The existing :class:`ft.Table` widget whose ``rows`` will be mutated.
        jobs: Current list of :class:`ConversionJob` objects.
        on_update: Callback to force a UI refresh after the table is updated.
    """
    # Keep header row (index 0)
    header = table.rows[0] if table.rows else None

    table.rows.clear()
    if header:
        table.rows.append(header)

    for job in jobs:
        builder = _JobRowBuilder(job, on_update)
        new_row = ft.TableRow(cells=builder.cells)  # type: ignore[arg-type]
        table.rows.append(new_row)
