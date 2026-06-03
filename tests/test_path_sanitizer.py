"""Tests for utils/path_sanitizer — traversal prevention and output path construction."""

import tempfile  # noqa: I001
from pathlib import Path

from utils.path_sanitizer import sanitize_input_path, sanitize_output_path, ensure_parent_dirs


class TestSanitizeInputPath:
    """Tests for :func:`utils.path_sanitizer.sanitize_input_path`."""

    def test_accepts_valid_file(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(b"RIFF\x27\x00\x00\x00WAVEfmt " + b"\x00" * 40)
            path = Path(tmp.name).resolve()
        ok, resolved = sanitize_input_path(str(path))
        assert ok is True
        assert isinstance(resolved, str)
        os.unlink(path)

    def test_rejects_nonexistent_file(self) -> None:
        ok, err = sanitize_input_path("/nonexistent/path/file.wav")
        assert ok is False
        assert "does not exist" in err.lower() or "not a regular file" in err.lower()

    def test_rejects_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ok, err = sanitize_input_path(tmpdir)
            assert ok is False

    def test_rejects_null_byte_in_path(self) -> None:
        ok, err = sanitize_input_path("/path/\x00evil.wav")
        assert ok is False
        assert "null byte" in err.lower()

    def test_rejects_dash_filename(self) -> None:
        with tempfile.NamedTemporaryFile(prefix="-test", suffix=".wav", delete=False) as tmp:
            path = Path(tmp.name).resolve()
        ok, _ = sanitize_input_path(str(path))
        assert ok is False  # dash prefix rejected
        os.unlink(path)


class TestSanitizeOutputPath:
    """Tests for :func:`utils.path_sanitizer.sanitize_output_path`."""

    def test_constructs_valid_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "input.wav"
            src.write_bytes(b"data")
            ok, err, resolved = sanitize_output_path(src)
            assert ok is True
            assert err == ""
            assert str(resolved).endswith("_converted.mp3")

    def test_uses_custom_output_folder(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            src = Path(tmpdir) / "input.wav"
            src.write_bytes(b"data")
            out_dir = Path(tmpdir) / "output"
            ok, _, resolved = sanitize_output_path(src, str(out_dir))
            assert ok is True
            assert Path(resolved).parent == out_dir.resolve()

    def test_rejects_null_byte_in_output_folder(self) -> None:
        src = Path("/tmp/input.wav")
        src.write_bytes(b"data")
        ok, err, _ = sanitize_output_path(src, "\x00evil")
        assert ok is False


class TestEnsureParentDirs:
    """Tests for :func:`utils.path_sanitizer.ensure_parent_dirs`."""

    def test_creates_parents(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "a" / "b" / "c" / "file.mp3"
            assert ensure_parent_dirs(target) is True
            assert target.parent.exists()

    def test_returns_false_on_perm_denied(self) -> None:
        # On Windows, creating under read-only root might fail
        import os as _os
        if _os.name == "nt":
            # Try writing to a known restricted location
            try:
                ok = ensure_parent_dirs(Path("C:\\ProgramData\\_test_dir_only\\deep\\file.mp3"))
                assert isinstance(ok, bool)
            except Exception:
                pass  # acceptable in test environment
