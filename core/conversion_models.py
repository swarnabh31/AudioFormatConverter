"""Pydantic data models for the conversion pipeline."""

import uuid  # noqa: D100
from datetime import datetime, timezone  # noqa: I001
from enum import Enum  # noqa: F401
from pathlib import Path  # noqa: F401
from typing import Optional  # noqa: F401

from pydantic import BaseModel, Field  # noqa: E0611


class JobStatus(str, Enum):
    """Possible processing states for a single ConversionJob."""

    QUEUED = "Queued"
    CONVERTING = "Converting"
    DONE = "Done"
    ERROR = "Error"


class ConversionSettings(BaseModel):
    """Encoder settings applied to every file in a batch run.

    Attributes:
        bitrate: Output MP3 bitrate in kbps (64–320).
        sample_rate: Output sample rate in Hz (must be 44100 or 48000).
        channel_mode: ``"mono"`` for single-channel downmix, ``"stereo"`` for two channels.
    """

    bitrate: int = Field(default=192, ge=64, le=320, description="Output MP3 bitrate in kbps")
    sample_rate: int = Field(default=44100, description="Output sample rate in Hz")
    channel_mode: str = Field(default="stereo", description="mono or stereo")

    class Config:
        """Pydantic V2 config shim for legacy compatibility."""

        arbitrary_types_allowed = True


class ConversionJob(BaseModel):
    """Represents one file queued for conversion.

    ``source_path`` and ``output_path`` are effectively immutable once the job is created.
    ``status``, ``progress_pct``, and ``error_message`` are updated in-place during processing.

    Attributes:
        id: UUID4 identifier unique to this job.
        source_path: Resolved :class:`Path` to the input audio file.
        output_path: Resolved :class:`Path` where the MP3 will be written.
        original_size_bytes: Size of the source file in bytes (captured at creation time).
        original_format: Lowercased extension string, e.g. ``"wav"``.
        settings: Encoder :class:`ConversionSettings` captured at enqueue time.
        status: Current processing state (starts as :attr:`JobStatus.QUEUED`).
        progress_pct: Percentage complete (0.0–100.0); updated during conversion.
        error_message: Set on failure; ``None`` when conversion succeeds.
        created_at: UTC timestamp of queue insertion.
    """

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    source_path: Path
    output_path: Path
    original_size_bytes: int
    original_format: str
    settings: ConversionSettings
    status: JobStatus = JobStatus.QUEUED
    progress_pct: float = 0.0
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def update_status(self, status: JobStatus, progress: Optional[float] = None,
                      error: Optional[str] = None) -> None:
        """Mutate status, progress, and/or error_message fields in place.

        Args:
            status: New :class:`JobStatus`.
            progress: New ``progress_pct`` (0–100); passed as ``None`` to skip update.
            error: Error message string; passed as ``None`` to skip update.
        """
        self.status = status
        if progress is not None:
            self.progress_pct = max(0.0, min(100.0, float(progress)))
        if error is not None:
            self.error_message = error
