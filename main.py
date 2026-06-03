"""Sovereign Audio Format Converter — Main Application Entry Point.

A desktop GUI built with Flet that batch-converts WAV, FLAC, M4A, and OGG files
to compressed MP3 using FFmpeg (via subprocess) as the encoding engine.
"""

import os  # noqa: D100
import sys  # noqa: I001
from pathlib import Path  # noqa: F401
from typing import Any, List, Optional  # noqa: F401

import flet as ft  # type: ignore[import-untyped]

# Ensure the project root is on sys.path so imports like `core.conversion_engine` resolve.
_project_root = Path(__file__).resolve().parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from utils.ffmpeg_detector import detect_ffmpeg, validate_version  # noqa: E402
from utils.config_loader import load_settings  # noqa: E402
from utils.file_helpers import human_size  # noqa: E402
from core.conversion_models import ConversionJob, ConversionSettings, JobStatus  # noqa: E402
from core.conversion_queue import ConversionQueue  # noqa: E402
from gui.theme import (
    ACCENT_PRIMARY,
    ACCENT_SUCCESS,
    ACCENT_TEXT,
    DARK_BG,
    FONT_FAMILY,
)
from gui.drag_drop_zone import create_drag_drop_zone  # noqa: E402
from gui.file_table import refresh_file_table  # noqa: E402
from gui.settings_panel import BITRATE_OPTIONS, SAMPLE_RATE_OPTIONS, create_settings_panel  # noqa: E402
from gui.batch_controls import create_batch_controls, update_button_states  # noqa: E402
from gui.progress_bar import create_progress_bar, refresh_progress_bar  # noqa: E402


class AudioConverterApp:
    """Top-level Flet application — bootstraps FFmpeg validation, UI, and conversion lifecycle."""

    def __init__(self, page: ft.Page) -> None:
        """Initialise the application state.

        Args:
            page: The Flet :class:`Page` instance to host the UI in.
        """
        self.page = page
        self.jobs: List[ConversionJob] = []
        self.queue: Optional[ConversionQueue] = None
        self.settings: ConversionSettings = ConversionSettings()  # defaults from config
        self.is_converting: bool = False
        self.output_folder: str = ""

        # UI widget references (populated in _build_layout)
        self.table: Optional[ft.Table] = None
        self.overall_bar: Optional[ft.ProgressBar] = None
        self.overall_label: Optional[ft.Text] = None
        self.per_file_controls: List[ft.Control] = []
        self.convert_btn: Optional[ft.ElevatedButton] = None
        self.clear_btn: Optional[ft.OutlinedButton] = None
        self.open_out_btn: Optional[ft.TextButton] = None
        self.status_bar: Optional[ft.Text] = None

    # ------------------------------------------------------------------ Startup

    def _validate_ffmpeg(self) -> bool:
        """Detect and validate FFmpeg.  Shows a modal error and exits on failure.

        Returns:
            ``True`` when FFmpeg is found and >= 4.0.0.
        """
        ffmpeg_path = detect_ffmpeg()
        if not ffmpeg_path:
            self._show_error_modal(
                "FFmpeg Not Found",
                "FFmpeg must be installed and on your system PATH to use this application.\n\n"
                "Download it from https://ffmpeg.org/download.html\n\n"
                "After installation, restart this application.",
            )
            return False

        ok, version_str = validate_version(ffmpeg_path if ffmpeg_path != "ffmpeg" else "ffmpeg")
        if not ok:
            self._show_error_modal(
                "FFmpeg Version Too Old",
                f"{version_str}\n\n"
                "A minimum FFmpeg version of 4.0 is required.\n"
                "Please upgrade your installation and restart.",
            )
            return False

        # Success — write detected path to env for downstream consumers
        os.environ["FFMPEG_PATH"] = str(ffmpeg_path)
        return True

    def _load_app_settings(self) -> None:
        """Load application settings and apply defaults.

        Reads ``config/settings.json`` via :func:`utils.config_loader.load_settings`
        and initialises the in-memory :class:`ConversionSettings`.
        """
        app_cfg = load_settings()
        self.settings = ConversionSettings(
            bitrate=int(app_cfg.get("default_bitrate", 192)),
            sample_rate=int(app_cfg.get("default_sample_rate", 44100)),
            channel_mode=str(app_cfg.get("default_channel_mode", "stereo")),
        )
        output_folder = app_cfg.get("output_folder")
        if isinstance(output_folder, str) and output_folder:
            self.output_folder = output_folder
        else:
            self.output_folder = ""

    # ------------------------------------------------------------------ UI helpers

    def _show_error_modal(self, title: str, message: str) -> None:
        """Display a blocking error dialog."""
        self.page.dialog = ft.AlertDialog(
            title=ft.Text(title, color="#FF1744"),
            content=ft.Text(message, size=14),
            bgcolor=DARK_BG,
            title_color="#FF1744",
            content_color=ACCENT_TEXT,
        )
        self.page.dialog.open = True  # type: ignore[attr-defined]
        self.page.update()

    def _show_info_modal(self, title: str, message: str) -> None:
        """Display a non-blocking information dialog."""
        self.page.dialog = ft.AlertDialog(
            title=ft.Text(title, color=ACCENT_PRIMARY),
            content=ft.Text(message, size=14),
            bgcolor=DARK_BG,
            title_color=ACCENT_PRIMARY,
            content_color=ACCENT_TEXT,
            buttons=[
                ft.ElevatedButton("OK", on_click=lambda _: self._close_dialog()),
            ],
        )
        self.page.dialog.open = True  # type: ignore[attr-defined]
        self.page.update()

    def _close_dialog(self) -> None:
        """Close the current dialog and refresh."""
        if self.page.dialog:
            self.page.dialog.open = False  # type: ignore[attr-defined]
            self.page.update()

    def _show_status(self, message: str) -> None:
        """Update the status-bar text at the bottom of the window."""
        if self.status_bar:
            self.status_bar.value = message
            self.status_bar.update()

    # ------------------------------------------------------------------ Layout

    def _build_layout(self) -> None:
        """Compose the single-page UI layout and attach it to the page."""
        self.page.title = "Sovereign Audio Converter"
        self.page.theme_mode = ft.ThemeMode.DARK  # type: ignore[attr-defined]

        header = ft.Row([
            ft.Icon(ft.icons.AUDIT_BOX, size=32, color=ACCENT_PRIMARY),
            ft.Text("Sovereign Audio Converter", size=24, weight="bold", color=ACCENT_TEXT),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=12)

        zone = create_drag_drop_zone(self._on_files_received)

        settings_col = create_settings_panel(self.settings, self._on_settings_changed)

        self.table = ft.Table(
            border=ft.border.all(1, "#9E9E9E"),
            border_radius=8,
            horizontal_margin=4,
        )
        # Header row
        header_row = ft.TableRow(cells=[
            ft.Text("Filename", style=ft.TextStyle(color=ACCENT_TEXT, weight="bold", size=12)),
            ft.Text("Format", style=ft.TextStyle(color=ACCENT_TEXT, weight="bold", size=12)),
            ft.Text("Size", style=ft.TextStyle(color=ACCENT_TEXT, weight="bold", size=12)),
            ft.Text("Progress", style=ft.TextStyle(color=ACCENT_TEXT, weight="bold", size=12)),
            ft.Text("Status", style=ft.TextStyle(color=ACCENT_TEXT, weight="bold", size=12)),
        ])
        self.table.rows.append(header_row)

        self.overall_bar = ft.ProgressBar(value=0.0, color="white", bgcolor="#333344", border_radius=8, width=600)
        self.overall_label = ft.Text("Overall: 0%", size=12, color="#9E9E9E")

        self.convert_btn, self.clear_btn, self.open_out_btn = self._build_batch_buttons()

        progress_col = ft.Column(controls=[
            self.overall_bar, self.overall_label,
        ], spacing=6)

        self.status_bar = ft.Text("Ready", size=12, color="#9E9E9E")

        main_content = ft.Container(
            content=ft.Column([
                header,
                ft.Divider(height=2, color="#333344"),
                ft.Row([zone, settings_col], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                ft.Divider(height=2, color="#333344"),
                self.table,
                progress_col,
                self._build_batch_buttons(),
            ],
                scroll=ft.ScrollMode.AUTO,
                spacing=16,
            ),
            expand=True,
            padding=20,
        )

        self.page.add(main_content)
        self.page.update()

    def _build_batch_buttons(self) -> tuple[ft.ElevatedButton, ft.OutlinedButton, ft.TextButton]:
        """Create batch control buttons and return them as a tuple."""
        cb = ft.ElevatedButton(
            "Convert All",
            icon=ft.icons.PLAY_ARROW,
            bgcolor=ACCENT_PRIMARY,
            color="white",
            disabled=True,
        )

        self.convert_btn = cb  # store reference

        def _on_convert(e: ft.ControlEvent) -> None:
            if self.jobs and not self.is_converting:
                self.page.run_task(self._do_convert_all)

        def _on_clear(e: ft.ControlEvent) -> None:
            if not self.is_converting:
                self.jobs.clear()
                self.queue = ConversionQueue()
                refresh_file_table(self.table, self.jobs, lambda: self.page.update())
                refresh_progress_bar(
                    self.overall_bar,  # type: ignore[arg-type]
                    self.overall_label,  # type: ignore[arg-type]
                    self.per_file_controls,
                    self.jobs,
                    lambda: self.page.update(),
                )
                update_button_states(self.convert_btn, self.clear_btn, self.open_out_btn,
                                     bool(self.jobs), self.is_converting, False)

        ob = ft.TextButton("Open Output Folder", icon=ft.icons.FOLDER_OPEN)

        def _on_open_output(e: ft.ControlEvent) -> None:
            self._open_output_folder()

        # Patch the on_click after creation (Flet sometimes needs it wired at runtime)
        cb.on_click = _on_convert  # type: ignore[attr-defined]
        ob.on_click = _on_open_output  # type: ignore[attr-defined]

        return (cb, ft.OutlinedButton("Clear Queue", icon=ft.icons.DELETE_SWEET_OUTLINE, on_click=_on_clear), ob)

    # ------------------------------------------------------------------ Handlers

    def _on_files_received(self, file_paths: List[str]) -> None:
        """Process a list of dropped/browsed file paths.

        Validates each path, creates a :class:`ConversionJob`, and updates the UI.
        """
        valid_jobs: List[ConversionJob] = []
        for fp in file_paths:
            if not Path(fp).is_file():
                continue
            # Re-validate magic bytes quickly
            from utils.file_helpers import validate_file  # noqa: E402
            vresult = validate_file(Path(fp))
            if not vresult.get("valid"):
                continue

            job = ConversionJob(
                source_path=Path(fp).resolve(),
                output_path=Path(""),  # set later by queue
                original_size_bytes=Path(fp).stat().st_size,
                original_format=Path(fp).suffix.lstrip(".").lower(),
                settings=self.settings.model_copy(),
            )
            valid_jobs.append(job)

        if not valid_jobs:
            self._show_info_modal("No Valid Files", "None of the dropped files were recognised as audio (WAV/FLAC/M4A/OGG).")
            return

        # Initialise queue on first use
        if self.queue is None:
            self.queue = ConversionQueue()

        # Add settings to existing jobs
        for job in valid_jobs:
            job.settings = self.settings.model_copy()

        self.jobs.extend(valid_jobs)
        self.queue.add_jobs(
            [str(j.source_path) for j in valid_jobs],
            self.settings,
        )

        refresh_file_table(self.table, self.jobs, lambda: self.page.update())
        refresh_progress_bar(
            self.overall_bar,  # type: ignore[arg-type]
            self.overall_label,  # type: ignore[arg-type]
            self.per_file_controls,
            self.jobs,
            lambda: self.page.update(),
        )
        update_button_states(self.convert_btn, self.clear_btn, self.open_out_btn,
                             bool(self.jobs), self.is_converting, False)

        self._show_status(f"Added {len(valid_jobs)} file(s) to queue")

    def _on_settings_changed(self, new_settings: ConversionSettings) -> None:
        """Update the current settings when a control changes."""
        self.settings = new_settings

    async def _do_convert_all(self) -> None:
        """Async coroutine — runs batch conversion on page.run_task (non-blocking)."""
        if not self.jobs or self.is_converting:
            return

        self.is_converting = True
        update_button_states(self.convert_btn, self.clear_btn, self.open_out_btn,
                             bool(self.jobs), True, False)
        self._show_status("Converting…")

        engine_imported = False
        try:
            from core.conversion_engine import ConversionEngine  # noqa: F811
            engine_imported = True
        except ImportError as exc:
            raise RuntimeError(f"ConversionEngine not available: {exc}") from exc

        engine = ConversionEngine(self.settings)
        semaphore = __import__("asyncio").Semaphore(1)

        async def _process_job(job: ConversionJob) -> None:
            async with semaphore:
                await engine.convert_file(job)  # type: ignore[attr-defined]
                # Push GUI update via page.run_on_gui_thread
                job_id = job.id
                status_val = job.status.value
                pct = job.progress_pct

                def _update() -> None:
                    refresh_file_table(self.table, self.jobs, lambda: self.page.update())
                    refresh_progress_bar(
                        self.overall_bar, self.overall_label,  # type: ignore[arg-type]
                        self.per_file_controls, self.jobs,
                        lambda: self.page.update(),
                    )

                await self.page.run_on_gui_thread(_update)

        jobs_to_process = [j for j in self.jobs if j.status == JobStatus.QUEUED]
        tasks = [asyncio.create_task(_process_job(j)) for j in jobs_to_process]
        await asyncio.gather(*tasks, return_exceptions=True)

        self.is_converting = False
        has_done = any(j.status == JobStatus.DONE for j in self.jobs)

        update_button_states(self.convert_btn, self.clear_btn, self.open_out_btn,
                             bool(self.jobs), False, has_done)

        done_count = sum(1 for j in self.jobs if j.status == JobStatus.DONE)
        err_count = sum(1 for j in self.jobs if j.status == JobStatus.ERROR)
        msg_parts = [f"Conversion complete."]
        if done_count:
            msg_parts.append(f"{done_count} done.")
        if err_count:
            msg_parts.append(f"{err_count} error(s).")
        self._show_status(" ".join(msg_parts))

        refresh_file_table(self.table, self.jobs, lambda: self.page.update())
        refresh_progress_bar(
            self.overall_bar, self.overall_label,  # type: ignore[arg-type]
            self.per_file_controls, self.jobs,
            lambda: self.page.update(),
        )

    def _open_output_folder(self) -> None:
        """Open the output directory in the system file explorer."""
        if not self.jobs:
            return
        # Use first job's output parent as default open target
        done_jobs = [j for j in self.jobs if j.status == JobStatus.DONE]
        if not done_jobs:
            self._show_status("No conversions complete yet.")
            return
        target_dir = str(done_jobs[0].output_path.parent)
        try:
            import subprocess  # noqa: D100
            subprocess.Popen(["explorer", target_dir], shell=True)  # type: ignore[arg-type]
        except Exception as exc:  # noqa: BLE001
            self._show_status(f"Could not open folder: {exc}")

    # ------------------------------------------------------------------ Bootstrap

    def run(self) -> None:
        """Full application bootstrap: detect FFmpeg → load settings → build UI."""
        if not self._validate_ffmpeg():
            sys.exit(1)

        self._load_app_settings()
        self.queue = ConversionQueue()
        self._build_layout()


def main() -> None:
    """Entry point — launch the Flet desktop app."""
    app_instance = AudioConverterApp(ft.Page)  # type: ignore[arg-type]
    app_instance.run()


if __name__ == "__main__":
    main()
