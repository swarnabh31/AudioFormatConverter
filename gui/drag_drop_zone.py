"""Drag-and-drop zone widget factory."""

import os  # noqa: D100
from typing import Callable, List  # noqa: F401

import flet as ft  # noqa: D100

from gui.theme import (
    ACCENT_PRIMARY,
    ACCENT_SUBTITLE,
    ACCENT_TEXT,
    DARK_SURFACE,
    FONT_FAMILY,
)


# Accepted audio extensions (lower-case).
ACCEPTED_EXTENSIONS: set = {".wav", ".flac", ".m4a", ".ogg"}


def create_drag_drop_zone(
    on_files_received: Callable[[List[str]], None],
) -> ft.Container:
    """Build a drag-and-drop zone that accepts audio files.

    The zone shows a dashed border at rest and turns purple-on-hover when
    the user drags files over it.  On drop, files whose extension is in
    :data:`ACCEPTED_EXTENSIONS` are collected and passed to *on_files_received*.

    Args:
        on_files_received: Callback invoked with a ``list[str]`` of valid file paths.

    Returns:
        A :class:`ft.Container` ready to be placed into any layout column or row.
    """
    hover_border_color = ACCENT_PRIMARY
    normal_border_color = ACCENT_SUBTITLE

    inner_label = ft.Text(
        "Drag audio files here\nor click to browse",
        text_align=ft.TextAlign.CENTER,
        color=ACCENT_SUBTITLE,
        size=16,
        font_family=FONT_FAMILY,
    )

    drop_area = ft.DragAndDropArea(
        content=ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.FOLDER_OPEN, size=48, color=ACCENT_SUBTITLE),
                inner_label,
            ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            border_radius=8,
            border=ft.border.all(2, normal_border_color, ft.border_style.dashed),
            padding=40,
        ),
        on_drag_enter=_on_drag_enter(hover_border_color),
        on_drag_leave=_on_drag_leave(normal_border_color),
        on_dropped=_on_drop(on_files_received),
    )

    browse_btn = ft.ElevatedButton(
        "Browse Files",
        icon=ft.icons.FILE_OPEN,
        bgcolor=ACCENT_PRIMARY,
        color="white",
        on_click=lambda _: _trigger_file_dialog(),
    )

    container = ft.Container(
        content=ft.Column([
            drop_area,
            ft.Row([browse_btn], alignment=ft.MainAxisAlignment.CENTER),
        ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=16,
        ),
        bgcolor=DARK_SURFACE,
        border_radius=8,
        padding=24,
    )

    return container


def _on_drag_enter(hover_color: str) -> Callable:
    """Factory returning a DragEnter event handler that highlights the zone."""

    def handler(e: ft.DragAndDropAreaOnDragOverEvent) -> None:
        e.control.border = ft.border.all(2, hover_color)
        e.control.update()

    return handler


def _on_drag_leave(normal_color: str) -> Callable:
    """Factory returning a DragLeave event handler that restores the normal border."""

    def handler(e: ft.DragAndDropAreaOnDragOverEvent) -> None:
        e.control.border = ft.border.all(2, normal_color)
        e.control.update()

    return handler


def _on_drop(on_files_received: Callable[[List[str]], None]) -> Callable:
    """Factory returning a drop event handler that filters and passes valid paths."""

    def handler(e: ft.DragAndDropAreaOnDroppedEvent) -> None:  # type: ignore[name-defined]
        if hasattr(e, "items") and e.items is not None:
            files: List[str] = []
            for item in e.items:  # type: ignore[attr-defined]
                if isinstance(item, str):
                    ext = os.path.splitext(item)[1].lower()
                    if ext in ACCEPTED_EXTENSIONS:
                        files.append(item)
                else:
                    files.append(str(item))
            on_files_received(files)
        e.control.border = ft.border.all(2, ACCENT_SUBTITLE)  # type: ignore[attr-defined]
        e.control.update()

    return handler


def _trigger_file_dialog() -> None:
    """Open a system file-picker dialog.  Results must be captured by the caller via page on_event binding."""
    pass  # This function is a placeholder — actual file picker logic goes in main.py's handler.
