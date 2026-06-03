"""Tests for core/conversion_models — Pydantic model validation."""

import pytest  # noqa: F401
from pathlib import Path

from core.conversion_models import ConversionJob, ConversionSettings, JobStatus


class TestConversionSettings:
    """Tests for :class:`core.conversion_models.ConversionSettings`."""

    def test_defaults(self) -> None:
        s = ConversionSettings()
        assert s.bitrate == 192
        assert s.sample_rate == 44100
        assert s.channel_mode == "stereo"

    def test_bitrate_bounds_low(self) -> None:
        with pytest.raises(Exception):  # pydantic ValidationError
            ConversionSettings(bitrate=63)

    def test_bitrate_bounds_high(self) -> None:
        with pytest.raises(Exception):
            ConversionSettings(bitrate=321)

    def test_channel_mode_must_be_mono_or_stereo(self) -> None:
        s = ConversionSettings(channel_mode="mono")
        assert s.channel_mode == "mono"

    def test_dunder_model_copy_works(self) -> None:
        s1 = ConversionSettings(bitrate=320)
        s2 = s1.model_copy()
        assert s2.bitrate == 320
        assert s1 is not s2


class TestConversionJob:
    """Tests for :class:`core.conversion_models.ConversionJob`."""

    def test_create_job(self) -> None:
        src = Path("/tmp/test.wav")
        out = Path("/tmp/test_converted.mp3")
        s = ConversionSettings(bitrate=128)
        job = ConversionJob(
            source_path=src,
            output_path=out,
            original_size_bytes=4096,
            original_format="wav",
            settings=s,
        )
        assert job.source_path == src
        assert job.output_path == out
        assert job.original_size_bytes == 4096
        assert job.status == JobStatus.QUEUED
        assert job.progress_pct == 0.0
        assert job.error_message is None

    def test_update_status(self) -> None:
        s = ConversionSettings()
        job = ConversionJob(
            source_path=Path("/tmp/t.wav"),
            output_path=Path("/tmp/t.mp3"),
            original_size_bytes=100,
            original_format="wav",
            settings=s,
        )
        job.update_status(JobStatus.CONVERTING, progress=45.5)
        assert job.status == JobStatus.CONVERTING
        assert job.progress_pct == 45.5

    def test_update_status_clamps_progress(self) -> None:
        s = ConversionSettings()
        job = ConversionJob(
            source_path=Path("/tmp/t.wav"),
            output_path=Path("/tmp/t.mp3"),
            original_size_bytes=100,
            original_format="wav",
            settings=s,
        )
        job.update_status(JobStatus.DONE, progress=200.0)
        assert job.progress_pct == 100.0

        job2 = ConversionJob(
            source_path=Path("/tmp/t.wav"),
            output_path=Path("/tmp/t.mp3"),
            original_size_bytes=100,
            original_format="wav",
            settings=s,
        )
        job2.update_status(JobStatus.ERROR, progress=-50.0)
        assert job2.progress_pct == 0.0
