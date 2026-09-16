"""
Unit tests for Cross-Platform Compatibility Layer (compat.py).
Tests Linux, Termux, macOS, and Windows runtime compatibility utilities.
"""

import sys
import os
import io
from pathlib import Path
from unittest.mock import patch, MagicMock

from aeo_graph_engine.compat import (
    is_windows,
    is_macos,
    is_linux,
    is_termux,
    is_wsl,
    get_platform_info,
    configure_utf8_streams,
    safe_print,
    open_browser,
    atomic_write_text,
    to_posix_path,
    resolve_path,
)


def test_get_platform_info():
    info = get_platform_info()
    assert isinstance(info, dict)
    assert "system_type" in info
    assert "is_windows" in info
    assert "is_macos" in info
    assert "is_linux" in info
    assert "is_termux" in info
    assert "is_wsl" in info
    assert "python_version" in info
    assert "default_encoding" in info
    assert "filesystem_encoding" in info


def test_termux_detection():
    with patch.dict(os.environ, {"TERMUX_VERSION": "0.118.0"}):
        assert is_termux() is True
        info = get_platform_info()
        assert info["system_type"] == "termux"

    with patch.dict(os.environ, {}, clear=True):
        with patch("os.path.exists", return_value=False):
            # When no termux vars and path doesn't exist
            if not ("TERMUX_VERSION" in os.environ or "PREFIX" in os.environ and "com.termux" in os.environ["PREFIX"]):
                assert is_termux() is False


def test_wsl_detection():
    with patch.dict(os.environ, {"WSL_DISTRO_NAME": "Ubuntu"}):
        with patch("aeo_graph_engine.compat.is_linux", return_value=True):
            assert is_wsl() is True


def test_configure_utf8_streams():
    # Should run without error on any OS
    configure_utf8_streams()


def test_safe_print_normal():
    buf = io.StringIO()
    safe_print("Hello", "World", 123, "⚡", file=buf)
    assert "Hello World 123 ⚡\n" == buf.getvalue()


def test_safe_print_unicode_error_handling():
    # Mock a stream that raises UnicodeEncodeError on write
    class StrictAsciiStream:
        def __init__(self):
            self.buffer = []
            self.encoding = "ascii"

        def write(self, text):
            if any(ord(c) > 127 for c in text):
                raise UnicodeEncodeError("ascii", text, 0, 1, "ordinal not in range(128)")
            self.buffer.append(text)

        def flush(self):
            pass

    stream = StrictAsciiStream()
    safe_print("Rocket 🚀 and Check ✅", file=stream)
    written = "".join(stream.buffer)
    assert "Rocket" in written
    assert "Check" in written


def test_atomic_write_text(tmp_path):
    target = tmp_path / "subdir" / "test_atomic.txt"
    content = "Hello, Cross-Platform World!\nLine 2 ⚡"
    
    written_path = atomic_write_text(target, content)
    assert written_path == target.resolve()
    assert target.exists()
    assert target.read_text(encoding="utf-8") == content

    # Test overwrite
    new_content = "Overwritten content 🚀"
    atomic_write_text(target, new_content)
    assert target.read_text(encoding="utf-8") == new_content


def test_to_posix_path():
    assert to_posix_path("dist/schema-graph.json") == "dist/schema-graph.json"
    assert to_posix_path(Path("a") / "b" / "c.txt") == "a/b/c.txt"


def test_resolve_path():
    p = resolve_path(".")
    assert p.is_absolute()
    assert p.exists()


def test_open_browser_termux():
    with patch("aeo_graph_engine.compat.is_termux", return_value=True):
        with patch("subprocess.run", return_value=MagicMock(returncode=0)) as mock_run:
            success = open_browser("http://127.0.0.1:8080/")
            assert success is True
            mock_run.assert_called_with(["termux-open-url", "http://127.0.0.1:8080/"], capture_output=True, text=True)


def test_open_browser_windows():
    with patch("aeo_graph_engine.compat.is_termux", return_value=False):
        with patch("aeo_graph_engine.compat.is_windows", return_value=True):
            with patch("os.startfile", create=True) as mock_startfile:
                success = open_browser("http://127.0.0.1:8080/")
                assert success is True
                mock_startfile.assert_called_with("http://127.0.0.1:8080/")


def test_open_browser_macos():
    with patch("aeo_graph_engine.compat.is_termux", return_value=False):
        with patch("aeo_graph_engine.compat.is_windows", return_value=False):
            with patch("aeo_graph_engine.compat.is_macos", return_value=True):
                with patch("subprocess.run", return_value=MagicMock(returncode=0)) as mock_run:
                    success = open_browser("http://127.0.0.1:8080/")
                    assert success is True
                    mock_run.assert_called_with(["open", "http://127.0.0.1:8080/"], capture_output=True, text=True)


def test_cli_platform_command(capsys):
    from aeo_graph_engine.cli import main
    ret = main(["--platform"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "AEO GRAPH ENGINE — PLATFORM COMPATIBILITY INFO" in captured.out
    assert "Operating System:" in captured.out
