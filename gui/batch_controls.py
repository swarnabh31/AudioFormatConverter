"""Batch action buttons — Convert All, Clear Queue, Open Output Folder."""

from typing import Callable  # noqa: F401

import flet as ft  # noqa: D100

from gui.theme import ACCENT_ERROR, ACCENT_PRIMARY, ACCENT_SUCCESS, ACCENT_TEXT, DARK_SURFACE


def create_batch_controls(
    on_convert: Callable[[], None],
    on_clear: Callable[[], None],
    on_open_output: Callable[[], None],
) -> ft.Row:
    """Build a :class:`ft.Row` with three action buttons.

    Args:
        on_convert: Callback for the "Convert All" button.
        on_clear: Callback for the "Clear Queue" button.
        on_open_output: Callback for the "Open Output Folder" button.

    Returns:
        A populated :class:`ft.Row` ready for insertion into the UI layout.
    """
    convert_btn = ft.ElevatedButton(
        "Convert All",
        icon=ft.icons.PLAY_ARROW,
        bgcolor=ACCENT_PRIMARY,
        color="white",
        on_click=lambda _: on_convert(),
    )

    clear_btn = ft.OutlinedButton(
        "Clear Queue",
        icon=ft.icons.DELETE_SWEET_OUTLINE,
        on_click=lambda _: on_clear(),
    )

    open_out_btn = ft.TextButton(
        "Open Output Folder",
        icon=ft.icons.FOLDER_OPEN,
        on_click=lambda _: on_open_output(),
    )

    row = ft.Row(
        controls=[convert_btn, clear_btn, open_out_btn],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=12,
    )

    return row


def update_button_states(
    convert_btn: ft.ElevatedButton,
    clear_btn: ft.OutlinedButton,
    open_out_btn: ft.TextButton,
    has_jobs: bool,
    is_running: bool,
    has_done: bool,
) -> None:
    """Update the enabled/disabled state and text of batch control buttons.

    Args:
        convert_btn: The "Convert All" button widget.
        clear_btn: The "Clear Queue" button widget.
        open_out_btn: The "Open Output Folder" button widget.
        has_jobs: ``True`` when the queue is non-empty.
        is_running: ``True`` while a conversion batch is in progress.
        has_done: ``True`` when at least one job has reached ``Done`` status.
    """
    convert_btn.disabled = is_running or not has_jobs
    clear_btn.disabled = not has_jobs or is_running
    open_out_btn.disabled = not has_done
    convert_btn.update()
    clear_btn.update()
    open_out_btn.update()
