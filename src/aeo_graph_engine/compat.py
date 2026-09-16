"""
Cross-Platform Compatibility Utilities for AEO Graph Engine.
Ensures seamless operation across Linux, Termux (Android), macOS, and Windows.
Zero external runtime dependencies.
"""

import sys
import os
import platform
import subprocess
import tempfile
import webbrowser
from pathlib import Path
from typing import Dict, Any, Union, Optional, List, TextIO


def is_windows() -> bool:
    """Returns True if running on Windows."""
    return os.name == "nt" or sys.platform.startswith("win")


def is_macos() -> bool:
    """Returns True if running on macOS (Darwin)."""
    return sys.platform == "darwin"


def is_linux() -> bool:
    """Returns True if running on Linux (including WSL and Termux)."""
    return sys.platform.startswith("linux")


def is_termux() -> bool:
    """Returns True if running within Termux on Android."""
    if "TERMUX_VERSION" in os.environ or "TERMUX_APP_PID" in os.environ:
        return True
    prefix = os.environ.get("PREFIX", "")
    if "com.termux" in prefix:
        return True
    return os.path.exists("/data/data/com.termux")


def is_wsl() -> bool:
    """Returns True if running inside Windows Subsystem for Linux (WSL)."""
    if not is_linux():
        return False
    # Check for Microsoft in /proc/version or WSL_DISTRO_NAME
    if "WSL_DISTRO_NAME" in os.environ or "WSL_INTEROP" in os.environ:
        return True
    try:
        if os.path.exists("/proc/version"):
            with open("/proc/version", "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().lower()
                return "microsoft" in content or "wsl" in content
    except Exception:
        pass
    return False


def get_platform_info() -> Dict[str, Any]:
    """
    Returns structured system platform information.
    """
    system_type = "unknown"
    if is_termux():
        system_type = "termux"
    elif is_wsl():
        system_type = "wsl"
    elif is_windows():
        system_type = "windows"
    elif is_macos():
        system_type = "macos"
    elif is_linux():
        system_type = "linux"

    return {
        "system_type": system_type,
        "is_windows": is_windows(),
        "is_macos": is_macos(),
        "is_linux": is_linux(),
        "is_termux": is_termux(),
        "is_wsl": is_wsl(),
        "os_name": os.name,
        "sys_platform": sys.platform,
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "default_encoding": sys.getdefaultencoding(),
        "filesystem_encoding": sys.getfilesystemencoding(),
    }


def configure_utf8_streams() -> None:
    """
    Ensures sys.stdin, sys.stdout, and sys.stderr handle UTF-8 cleanly
    with character replacement fallbacks on Windows legacy terminals and Termux.
    """
    for stream_name in ("stdin", "stdout", "stderr"):
        stream: Optional[TextIO] = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def safe_print(*args: Any, file: Optional[TextIO] = None, **kwargs: Any) -> None:
    """
    Safe print wrapper that catches UnicodeEncodeError on legacy consoles
    (e.g., Windows cp1252/cp437) and safely prints sanitized text.
    """
    target = file if file is not None else sys.stdout
    sep = kwargs.get("sep", " ")
    end = kwargs.get("end", "\n")
    flush = kwargs.get("flush", False)

    text = sep.join(str(a) for a in args)

    try:
        target.write(text + end)
        if flush:
            target.flush()
    except UnicodeEncodeError:
        # Fallback to ascii/latin-1 with replacement characters
        encoding = getattr(target, "encoding", None) or "utf-8"
        sanitized = text.encode(encoding, errors="replace").decode(encoding, errors="replace")
        try:
            target.write(sanitized + end)
            if flush:
                target.flush()
        except Exception:
            # Ultimate ASCII fallback
            ascii_text = text.encode("ascii", errors="replace").decode("ascii")
            target.write(ascii_text + end)
            if flush:
                target.flush()


def open_browser(url: str) -> bool:
    """
    Opens a URL in the user's default browser across Linux, Termux, macOS, and Windows.
    Returns True if launched successfully, False otherwise.
    """
    # 1. Termux on Android
    if is_termux():
        try:
            res = subprocess.run(["termux-open-url", url], capture_output=True, text=True)
            if res.returncode == 0:
                return True
        except Exception:
            pass

    # 2. Windows Native
    if is_windows():
        try:
            if hasattr(os, "startfile"):
                os.startfile(url)
                return True
        except Exception:
            pass

    # 3. macOS
    if is_macos():
        try:
            res = subprocess.run(["open", url], capture_output=True, text=True)
            if res.returncode == 0:
                return True
        except Exception:
            pass

    # 4. Standard Python webbrowser fallback
    try:
        if webbrowser.open(url):
            return True
    except Exception:
        pass

    # 5. Linux xdg-open fallback
    if is_linux():
        try:
            res = subprocess.run(["xdg-open", url], capture_output=True, text=True)
            if res.returncode == 0:
                return True
        except Exception:
            pass

    return False


def atomic_write_text(
    file_path: Union[str, Path],
    content: str,
    encoding: str = "utf-8",
    errors: str = "strict"
) -> Path:
    """
    Atomically writes text content to target file path.
    Handles temporary file replacement safely across Windows and POSIX filesystems.
    """
    dest = Path(file_path).resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Use temp file in the same directory to guarantee same filesystem on Unix & Windows
    temp_dir = dest.parent
    prefix = f".tmp_{dest.name}_"

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding=encoding,
        errors=errors,
        dir=temp_dir,
        delete=False,
        prefix=prefix
    ) as tf:
        tf.write(content)
        temp_name = tf.name

    try:
        if is_windows() and dest.exists():
            # On Windows os.replace handles atomic overwrite if not locked
            try:
                os.replace(temp_name, dest)
            except PermissionError:
                # If target is temporarily locked, try remove and rename
                try:
                    os.remove(dest)
                except Exception:
                    pass
                os.rename(temp_name, dest)
        else:
            os.replace(temp_name, dest)
    except Exception as e:
        # Clean up temporary file on failure
        if os.path.exists(temp_name):
            try:
                os.remove(temp_name)
            except Exception:
                pass
        raise e

    return dest


def to_posix_path(path: Union[str, Path]) -> str:
    """
    Converts a path object or string to POSIX style (forward slashes).
    Useful for consistent schema URLs and JSON manifest generation.
    """
    p = Path(path)
    return p.as_posix()


def resolve_path(path: Union[str, Path]) -> Path:
    """
    Resolves a path to its absolute canonical Path object.
    """
    return Path(path).expanduser().resolve()
