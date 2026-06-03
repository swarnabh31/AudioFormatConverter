"""FFmpeg subprocess-driven conversion engine with real-time progress extraction.

Uses `subprocess.Popen` directly (not pydub's wrapper) so we can tap FFmpeg's
stderr output for time-based progress information during encoding.
"""

import asyncio  # noqa: D100
import os  # noqa: D100
import re  # noqa: I001
import subprocess  # noqa: D100
from pathlib import Path  # noqa: F401
from typing import Any, Dict, List, Optional  # noqa: F401

from utils.path_sanitizer import sanitize_input_path, sanitize_output_path
from utils.format_mapper import get_ffmpeg_input_format
from core.conversion_models import ConversionJob, ConversionSettings, JobStatus


class ConversionError(Exception):
    """Raised when a file conversion step fails."""

    def __init__(self, message: str, job_id: Optional[str] = None) -> None:
        super().__init__(message)
        self.job_id: Optional[str] = job_id
        self.message: str = message


class ConversionEngine:
    """Drives FFmpeg subprocess encoding for one or more :class:`ConversionJob` instances.

    Attributes:
        settings: Encoder settings captured at engine construction time.  Jobs that are
            already running will **not** be affected by changes to the settings after the
            engine is created.
    """

    def __init__(self, settings: ConversionSettings) -> None:
        """Create a conversion engine with the given encoding parameters.

        Args:
            settings: Encoder :class:`ConversionSettings` that will govern every job run
                through this engine instance.
        """
        self.settings: ConversionSettings = settings

    def get_output_path(self, source: Path) -> Path:
        """Construct the output MP3 path for *source* in its own directory.

        Args:
            source: Source audio :class:`Path`.

        Returns:
            Resolved :class:`Path` to ``<stem>_converted.mp3`` in the source directory.
        """
        stem = source.stem
        output_folder = str(source.parent)
        ok, err, resolved = sanitize_output_path(source, output_folder)
        if not ok:
            raise ConversionError(f"Output path construction failed: {err}")
        return Path(resolved)

    async def convert_file(self, job: ConversionJob) -> ConversionJob:
        """Execute a single file conversion via FFmpeg subprocess.

        The method updates ``job.status``, ``job.progress_pct``, and
        ``job.error_message`` in place during processing.

        Args:
            job: :class:`ConversionJob` whose ``source_path`` and ``output_path`` fields
                are already populated.

        Returns:
            The same *job* object, mutated with final status/progress/error info.
        """
        try:
            # ---- 1. Validate source path ----
            src_ok, src_info = sanitize_input_path(str(job.source_path))
            if not src_ok:
                job.update_status(JobStatus.ERROR, error=f"Source validation failed: {src_info}")
                return job

            # ---- 2. Validate / construct output path ----
            out_ok, out_err, out_resolved = sanitize_output_path(job.source_path)
            if not out_ok:
                job.update_status(JobStatus.ERROR, error=f"Output path failed: {out_err}")
                return job
            job.output_path = Path(out_resolved)

            # ---- 3. Build FFmpeg command ----
            input_format: str = get_ffmpeg_input_format(job.source_path.suffix.lower())
            ac_value: int = 1 if self.settings.channel_mode == "mono" else 2

            ffmpeg_cmd: List[str] = [
                "ffmpeg",
                "-y",                           # overwrite output without asking
                "-f", input_format,             # force input format
                "-i", str(job.source_path),     # input file
                "-ar", str(self.settings.sample_rate),  # sample rate
                "-ac", str(ac_value),           # channel count
                "-b:a", f"{self.settings.bitrate}k",  # bitrate
                "-f", "mp3",                    # force output format
                str(job.output_path),           # output file
            ]

            # ---- 4. Get duration from ffprobe (once) ----
            total_duration: float = await self._get_duration(job.source_path)

            # ---- 5. Run FFmpeg with stderr progress extraction ----
            job.update_status(JobStatus.CONVERTING)
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"

            proc: subprocess.Popen = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                env=env,
                text=True,
            )

            stderr_chunks: List[str] = []

            while True:
                line: Optional[str] = proc.stderr.readline()
                if line == "" and proc.poll() is not None:
                    break
                if line:
                    stderr_chunks.append(line)
                    # Parse progress from FFmpeg stderr
                    current_time: Optional[float] = self._parse_progress_time(line)
                    if current_time is not None and total_duration > 0:
                        pct: float = (current_time / total_duration) * 100.0
                        job.update_status(JobStatus.CONVERTING, progress=pct)
                        await asyncio.sleep(0)  # yield control to event loop

            stdout_out: str = proc.stdout.read() if proc.stdout else ""
            proc.wait()

            # ---- 6. Evaluate result ----
            if proc.returncode == 0:
                job.update_status(JobStatus.DONE, progress=100.0)
            else:
                last_lines: List[str] = stderr_chunks[-5:] if stderr_chunks else []
                error_text: str = "\n".join(last_lines).strip() or "Unknown FFmpeg error"
                job.update_status(JobStatus.ERROR, error=f"FFmpeg exited with code {proc.returncode}: {error_text}")

            return job

        except FileNotFoundError:
            job.update_status(JobStatus.ERROR, error="FFmpeg binary not found on PATH")
            return job
        except subprocess.TimeoutExpired as exc:
            job.update_status(JobStatus.ERROR, error=f"Conversion timed out: {exc}")
            return job
        except Exception as exc:  # noqa: BLE001
            job.update_status(JobStatus.ERROR, error=str(exc))
            return job

    async def _get_duration(self, source_path: Path) -> float:
        """Return the audio duration in seconds by probing the file with ffprobe.

        Args:
            source_path: Path to the input audio file.

        Returns:
            Duration in floating-point seconds (``0.0`` on failure).
        """
        try:
            probe_cmd: List[str] = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(source_path),
            ]
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, _subprocess_capture, probe_cmd),
                timeout=10,
            )
            dur_str: str = result.strip()
            return float(dur_str) if dur_str else 0.0
        except (ValueError, asyncio.TimeoutExpired):
            return 0.0

    @staticmethod
    def _parse_progress_time(line: str) -> Optional[float]:
        """Extract elapsed time in seconds from an FFmpeg stderr line.

        Matches patterns like ``time=01:23:45.67`` or ``size=      XXXkB time=00:01:23.45``.

        Args:
            line: A single stderr output line from the FFmpeg subprocess.

        Returns:
            Elapsed time in seconds (float), or ``None`` if no match is found.
        """
        match = re.search(r"time=(\d+):(\d+):([\d.]+)", line)
        if not match:
            return None
        hours: int = int(match.group(1))
        minutes: int = int(match.group(2))
        seconds: float = float(match.group(3))
        return hours * 3600 + minutes * 60 + seconds


def _subprocess_capture(args: List[str]) -> str:
    """Helper run in a thread — capture stdout only."""
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=10)
        return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""
