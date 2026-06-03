"""Async bounded task queue for batch file conversions."""

import asyncio  # noqa: D100
from pathlib import Path  # noqa: D100
from typing import Any, List, Optional  # noqa: F401

from core.conversion_models import ConversionJob, ConversionSettings, JobStatus
from utils.path_sanitizer import sanitize_input_path, sanitize_output_path


class ConversionQueue:
    """Manages a bounded asyncio queue of :class:`ConversionJob` instances.

    Jobs are processed sequentially (bounded concurrency = 1 by default) to avoid
    FFmpeg CPU contention while keeping the Flet GUI event loop responsive.

    Attributes:
        max_concurrency: Maximum number of concurrent FFmpeg subprocesses (default 1).
    """

    MAX_CONCURRENCY: int = 1

    def __init__(self, max_concurrency: Optional[int] = None) -> None:
        """Create a conversion queue.

        Args:
            max_concurrency: Override the class default concurrency limit. ``None`` uses
                :attr:`MAX_CONCURRENCY`.
        """
        self._max_concurrency: int = max_concurrency or self.MAX_CONCURRENCY
        self._jobs: List[ConversionJob] = []
        self._semaphore: asyncio.Semaphore = asyncio.Semaphore(self._max_concurrency)

    @property
    def jobs(self) -> List[ConversionJob]:
        """Return the current list of queued/running/completed jobs."""
        return list(self._jobs)

    @property
    def is_empty(self) -> bool:
        """``True`` when there are no jobs in the queue."""
        return len(self._jobs) == 0

    @property
    def job_count(self) -> int:
        """Total number of jobs currently in the queue."""
        return len(self._jobs)

    def add_jobs(
        self,
        source_paths: List[str],
        settings: ConversionSettings,
    ) -> List[ConversionJob]:
        """Create and enqueue :class:`ConversionJob` instances for *source_paths*.

        Each valid path is sanitised, validated, and paired with the given *settings*.
        Invalid paths are silently skipped (no exception raised).

        Args:
            source_paths: Raw filesystem paths to add.
            settings: Encoder settings applied at enqueue time.

        Returns:
            List of newly created :class:`ConversionJob` objects.
        """
        new_jobs: List[ConversionJob] = []
        for raw_path in source_paths:
            ok, resolved = sanitize_input_path(raw_path)
            if not ok:
                continue  # skip invalid paths silently

            out_ok, out_err, out_resolved = sanitize_output_path(Path(resolved))
            if not out_ok:
                continue

            try:
                job = ConversionJob(
                    source_path=Path(resolved),
                    output_path=Path(out_resolved),
                    original_size_bytes=Path(resolved).stat().st_size,
                    original_format=Path(resolved).suffix.lstrip(".").lower(),
                    settings=settings.model_copy(),
                )
            except Exception:  # noqa: BLE001
                continue

            self._jobs.append(job)
            new_jobs.append(job)

        return new_jobs

    async def process_all(self, jobs: Optional[List[ConversionJob]] = None,
                          on_progress_cb: Any = None, on_job_complete_cb: Any = None,
                          page: Any = None) -> List[ConversionJob]:
        """Process every job in the queue (or *jobs* if provided).

        Runs jobs sequentially within a bounded concurrency semaphore so that at most
        :attr:`MAX_CONCURRENCY` FFmpeg instances execute simultaneously.

        Args:
            jobs: Specific job list to process; defaults to ``self._jobs``.
            on_progress_cb: Optional callback ``(job, progress_pct)`` for GUI updates.
            on_job_complete_cb: Optional callback ``(job)`` after each job finishes.
            page: Flet :class:`Page` instance (used to push GUI thread updates).

        Returns:
            The list of processed :class:`ConversionJob` instances.
        """
        target_jobs: List[ConversionJob] = jobs if jobs is not None else self._jobs
        engine_imported = False
        try:
            from core.conversion_engine import ConversionEngine  # noqa: F811
            engine_imported = True
        except ImportError as exc:  # pragma: no cover — only happens in unit-test stubs
            raise RuntimeError(f"ConversionEngine import failed: {exc}") from exc

        engine = ConversionEngine(target_jobs[0].settings) if target_jobs else None
        if not engine:
            return []

        sem: asyncio.Semaphore = asyncio.Semaphore(self._max_concurrency)
        tasks_to_wait: List[asyncio.Task] = []

        async def _run_job(job: ConversionJob) -> None:
            async with sem:
                await engine.convert_file(job)  # type: ignore[attr-defined]
                if on_job_complete_cb and page:
                    await page.run_on_gui_thread(
                        lambda j=job: on_job_complete_cb(j)
                    )

        for job in target_jobs:
            task = asyncio.create_task(_run_job(job))
            tasks_to_wait.append(task)

        await asyncio.gather(*tasks_to_wait, return_exceptions=True)
        return target_jobs

    def cancel_all(self) -> List[ConversionJob]:
        """Mark all pending jobs as cancelled and remove them from the queue.

        Returns:
            The list of removed jobs before clearing.
        """
        removed = list(self._jobs)
        self._jobs.clear()
        return removed
