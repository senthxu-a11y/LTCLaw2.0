# -*- coding: utf-8 -*-
"""CLI command: run LTCLAW-GY.X app on a free port in a native webview window."""
# pylint:disable=too-many-branches,too-many-statements,consider-using-with
from __future__ import annotations

import logging
import os
import socket
import subprocess
import sys
import threading
import time
import traceback
import webbrowser

import click

from ..constant import LOG_LEVEL_ENV, WORKING_DIR
from ..utils.logging import setup_logger

try:
    import webview
except ImportError:
    webview = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)
WINDOW_TITLE = "LTCLAW-GY.X Desktop"
GUI_RELAUNCH_ENV = "LTCLAW_GY_X_DESKTOP_GUI_RELAUNCHED"


def _ensure_wrapper_file_logger() -> None:
    """Persist desktop wrapper logs so window bootstrap failures are visible."""
    log_path = WORKING_DIR / "desktop_logs" / "desktop.wrapper.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    resolved = str(log_path.resolve())
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler) and getattr(
            handler, "baseFilename", None
        ) == resolved:
            return

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            "%(levelname)s %(name)s:%(lineno)d | %(asctime)s | %(message)s",
        )
    )
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)
    logger.propagate = True


class WebViewAPI:
    """API exposed to the webview for external links and file downloads."""

    def open_external_link(self, url: str) -> None:
        """Open URL in system's default browser."""
        if not url.startswith(("http://", "https://")):
            return
        webbrowser.open(url)

    def save_file(self, url: str, filename: str) -> bool:
        """Download a file from *url* and save it via a native save dialog.

        Shows the OS "Save As" dialog so the user can pick a destination,
        then downloads the file and writes it there.  This is the desktop
        equivalent of the browser's ``<a download>`` click pattern which
        pywebview/WebView2 does not support.

        Args:
            url: Full HTTP(S) URL of the file to download.
            filename: Default filename shown in the save dialog.

        Returns:
            True if the file was saved successfully, False if the user
            cancelled the dialog or an error occurred.
        """
        import re
        import shutil
        import urllib.request

        if not url.startswith(("http://", "https://")):
            return False

        # Sanitize filename: remove characters illegal on Windows
        # (< > : " / \ | ? *) and trim leading/trailing whitespace/dots.
        # Colons are common in backup names like "Backup 2026-04-22 17:36".
        safe_name = re.sub(r'[<>:"/\\|?*]', "_", filename).strip(" .")

        try:
            # Show native OS save dialog via pywebview
            result = webview.windows[0].create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=safe_name,
            )
            if not result:
                return False  # user cancelled

            dest_path = result if isinstance(result, str) else result[0]

            # Download from the local backend and write to chosen path
            with urllib.request.urlopen(url) as response:
                with open(dest_path, "wb") as f:
                    shutil.copyfileobj(response, f)

            return True
        except Exception:
            logger.exception("save_file failed")
            return False


def _find_free_port(host: str = "127.0.0.1") -> int:
    """Bind to port 0 and return the OS-assigned free port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        sock.listen(1)
        return sock.getsockname()[1]


def _wait_for_http(host: str, port: int, timeout_sec: float = 300.0) -> bool:
    """Return True once /api/version answers 200 (not just TCP open)."""
    import urllib.error
    import urllib.request
    deadline = time.monotonic() + timeout_sec
    url = f"http://{host}:{port}/api/version"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2.0) as resp:
                if 200 <= resp.status < 300:
                    return True
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(1)
    return False


def _get_windows_gui_python() -> str | None:
    """Return sibling pythonw.exe when available."""
    if not sys.platform.startswith("win"):
        return None

    exe_path = os.path.abspath(sys.executable)
    exe_dir = os.path.dirname(exe_path)
    gui_python = os.path.join(exe_dir, "pythonw.exe")
    if os.path.exists(gui_python):
        return gui_python
    return None


def _relaunch_with_pythonw_if_needed(host: str, log_level: str) -> bool:
    """Re-launch under pythonw on Windows so desktop mode is truly GUI-first."""
    if not sys.platform.startswith("win"):
        return False
    if os.environ.get(GUI_RELAUNCH_ENV) == "1":
        return False

    exe_name = os.path.basename(sys.executable).lower()
    if exe_name == "pythonw.exe":
        return False

    gui_python = _get_windows_gui_python()
    if not gui_python:
        logger.warning("pythonw.exe not found next to %s", sys.executable)
        return False

    env = os.environ.copy()
    env[GUI_RELAUNCH_ENV] = "1"
    creationflags = 0
    detached_process = getattr(subprocess, "DETACHED_PROCESS", 0)
    create_new_process_group = getattr(
        subprocess,
        "CREATE_NEW_PROCESS_GROUP",
        0,
    )
    creationflags |= detached_process | create_new_process_group
    subprocess.Popen(
        [
            gui_python,
            "-m",
            "ltclaw_gy_x",
            "desktop",
            "--host",
            host,
            "--log-level",
            log_level,
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
        cwd=os.getcwd(),
        creationflags=creationflags,
        close_fds=True,
    )
    logger.info("Desktop re-launched via pythonw.exe")
    click.echo("Desktop launcher detached to pythonw.exe")
    return True


def _focus_window_on_windows(window_title: str) -> None:
    """Best-effort foreground restore for the desktop window."""
    if not sys.platform.startswith("win"):
        return

    def _worker() -> None:
        user32 = getattr(getattr(__import__("ctypes"), "windll", None), "user32", None)
        if user32 is None:
            return

        sw_restore = 9
        sw_show = 5
        for _ in range(20):
            hwnd = user32.FindWindowW(None, window_title)
            if hwnd:
                user32.ShowWindow(hwnd, sw_restore)
                user32.ShowWindow(hwnd, sw_show)
                user32.SetForegroundWindow(hwnd)
                user32.BringWindowToTop(hwnd)
                user32.SetActiveWindow(hwnd)
                logger.info("Desktop window focused, hwnd=%s", hwnd)
                return
            time.sleep(0.5)
        logger.warning("Unable to locate desktop window for foreground restore")

    threading.Thread(
        target=_worker,
        name="desktop-window-focus",
        daemon=True,
    ).start()


@click.command("desktop")
@click.option(
    "--host",
    default="127.0.0.1",
    show_default=True,
    help="Bind host for the app server.",
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(
        ["critical", "error", "warning", "info", "debug", "trace"],
        case_sensitive=False,
    ),
    show_default=True,
    help="Log level for the app process.",
)
def desktop_cmd(
    host: str,
    log_level: str,
) -> None:
    """Run LTCLAW-GY.X app on an auto-selected free port in a webview window.

    Starts the FastAPI app in a subprocess on a free port, then opens a
    native webview window loading that URL. Use for a dedicated desktop
    window without conflicting with an existing LTCLAW-GY.X app instance.
    """
    # Setup logger for desktop command (separate from backend subprocess)
    setup_logger(log_level)
    _ensure_wrapper_file_logger()
    if _relaunch_with_pythonw_if_needed(host, log_level):
        return

    port = _find_free_port(host)
    url = f"http://{host}:{port}"
    click.echo(f"Starting LTCLAW-GY.X app on {url} (port {port})")
    logger.info("Server subprocess starting...")

    env = os.environ.copy()
    env[LOG_LEVEL_ENV] = log_level
    storage_path = str((WORKING_DIR / ".desktop_webview2").resolve())
    os.makedirs(storage_path, exist_ok=True)

    if "SSL_CERT_FILE" in env:
        cert_file = env["SSL_CERT_FILE"]
        if os.path.exists(cert_file):
            logger.info(f"SSL certificate: {cert_file}")
        else:
            logger.warning(
                f"SSL_CERT_FILE set but not found: {cert_file}",
            )
    else:
        logger.warning("SSL_CERT_FILE not set on environment")

    desktop_log_dir = WORKING_DIR / "desktop_logs"
    desktop_log_dir.mkdir(parents=True, exist_ok=True)
    backend_stdout = open(
        desktop_log_dir / "backend.stdout.log",
        "a",
        encoding="utf-8",
    )
    backend_stderr = open(
        desktop_log_dir / "backend.stderr.log",
        "a",
        encoding="utf-8",
    )
    proc = None
    manually_terminated = (
        False  # Track if we intentionally terminated the process
    )
    try:
        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "ltclaw_gy_x",
                "app",
                "--host",
                host,
                "--port",
                str(port),
                "--log-level",
                log_level,
            ],
            stdin=subprocess.DEVNULL,
            stdout=backend_stdout,
            stderr=backend_stderr,
            env=env,
            bufsize=1,
            universal_newlines=True,
        )
        try:
            logger.info("Waiting for HTTP ready...")
            if _wait_for_http(host, port):
                logger.info("HTTP ready, creating webview window...")
                api = WebViewAPI()
                window = webview.create_window(
                    WINDOW_TITLE,
                    url,
                    width=1280,
                    height=800,
                    focus=True,
                    text_select=True,
                    js_api=api,
                )
                logger.info("Webview window created: %s", window)
                logger.info(
                    "Calling webview.start() (blocks until closed)...",
                )
                start_kwargs = {
                    "private_mode": False,
                    "storage_path": storage_path,
                    "debug": log_level.lower() == "debug",
                }
                if sys.platform.startswith("win"):
                    start_kwargs["gui"] = "edgechromium"
                logger.info("webview.start kwargs: %s", start_kwargs)
                webview.start(
                    lambda: _focus_window_on_windows(WINDOW_TITLE),
                    **start_kwargs,
                )  # blocks until user closes the window
                logger.info("webview.start() returned (window closed).")
            else:
                logger.error("Server did not become ready in time.")
                click.echo(
                    "Server did not become ready in time; open manually: "
                    + url,
                    err=True,
                )
                try:
                    proc.wait()
                except KeyboardInterrupt:
                    pass  # will be handled in finally
        finally:
            # Ensure backend process is always cleaned up
            # Wrap all cleanup operations to handle race conditions:
            # - Process may exit between poll() and terminate()
            # - terminate()/kill() may raise ProcessLookupError/OSError
            # - We must not let cleanup exceptions mask the original error
            if proc and proc.poll() is None:  # process still running
                logger.info("Terminating backend server...")
                manually_terminated = (
                    True  # Mark that we're intentionally terminating
                )
                try:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5.0)
                        logger.info("Backend server terminated cleanly.")
                    except subprocess.TimeoutExpired:
                        logger.warning(
                            "Backend did not exit in 5s, force killing...",
                        )
                        try:
                            proc.kill()
                            proc.wait()
                            logger.info("Backend server force killed.")
                        except (ProcessLookupError, OSError) as e:
                            # Process already exited, which is fine
                            logger.debug(
                                f"kill() raised {e.__class__.__name__} "
                                f"(process already exited)",
                            )
                except (ProcessLookupError, OSError) as e:
                    # Process already exited between poll() and terminate()
                    logger.debug(
                        f"terminate() raised {e.__class__.__name__} "
                        f"(process already exited)",
                    )
            elif proc:
                logger.info(
                    f"Backend already exited with code {proc.returncode}",
                )

        # Only report errors if process exited unexpectedly
        # (not manually terminated)
        # On Windows, terminate() doesn't use signals so exit codes vary
        # (1, 259, etc.)
        # On Unix/Linux/macOS, terminate() sends SIGTERM (exit code -15)
        # Using a flag is more reliable than checking specific exit codes
        if proc and proc.returncode != 0 and not manually_terminated:
            logger.error(
                f"Backend process exited unexpectedly with code "
                f"{proc.returncode}",
            )
            # Follow POSIX convention for exit codes:
            # - Negative (signal): 128 + signal_number
            # - Positive (normal): use as-is
            # Example: -15 (SIGTERM) -> 143 (128+15), -11 (SIGSEGV) ->
            # 139 (128+11)
            if proc.returncode < 0:
                sys.exit(128 + abs(proc.returncode))
            else:
                sys.exit(proc.returncode or 1)
    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt in main, cleaning up...")
        raise
    except Exception as e:
        logger.error(f"Exception: {e!r}")
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        raise
    finally:
        backend_stdout.close()
        backend_stderr.close()
