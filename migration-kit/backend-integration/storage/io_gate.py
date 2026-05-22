from __future__ import annotations

import hashlib
import os
import tempfile
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.storage.store_registry import resolve_registered_store_paths

if os.name == "nt":
    import msvcrt
else:
    import fcntl


_LOCK_FILE_NAME = ".storage-io.lock"
_PROCESS_GATE = threading.RLock()
_STATE_GUARD = threading.RLock()
_LOCK_DEPTH = 0
_LOCK_HANDLE: object | None = None


def storage_io_lock_path() -> Path:
    resolved_targets = sorted(
        ((name, path.resolve()) for name, path in resolve_registered_store_paths()),
        key=lambda item: item[0],
    )
    digest_input = "\n".join(f"{name}={path}" for name, path in resolved_targets)
    digest = hashlib.sha256(digest_input.encode("utf-8")).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / "swaif-storage-locks" / f"{digest}{_LOCK_FILE_NAME}"


def _lock_file(handle: object, timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds

    while True:
        try:
            if os.name == "nt":
                file_handle = handle
                file_handle.seek(0)
                if file_handle.seek(0, os.SEEK_END) == 0:
                    file_handle.write(b"0")
                    file_handle.flush()
                file_handle.seek(0)
                msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                file_handle = handle
                fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except OSError:
            if time.monotonic() >= deadline:
                raise RuntimeError(
                    "Timed out waiting for the shared storage I/O lock. "
                    "Another process is still running backup, restore, or a JSON write."
                ) from None
            time.sleep(0.05)


def _unlock_file(handle: object) -> None:
    if os.name == "nt":
        file_handle = handle
        file_handle.seek(0)
        msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        file_handle = handle
        fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def hold_storage_io_lock(*, timeout_seconds: float = 30.0) -> Iterator[None]:
    global _LOCK_DEPTH, _LOCK_HANDLE

    with _PROCESS_GATE:
        with _STATE_GUARD:
            if _LOCK_DEPTH > 0:
                _LOCK_DEPTH += 1
                nested = True
            else:
                nested = False

        if nested:
            try:
                yield
            finally:
                with _STATE_GUARD:
                    _LOCK_DEPTH -= 1
            return

        handle = None
        lock_acquired = False
        try:
            lock_path = storage_io_lock_path()
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            handle = lock_path.open("a+b")
            _lock_file(handle, timeout_seconds)
            lock_acquired = True
            with _STATE_GUARD:
                _LOCK_HANDLE = handle
                _LOCK_DEPTH = 1
            yield
        finally:
            with _STATE_GUARD:
                if _LOCK_DEPTH > 0:
                    _LOCK_DEPTH -= 1
                should_release = _LOCK_DEPTH == 0 and _LOCK_HANDLE is not None
                active_handle = _LOCK_HANDLE if should_release else None
                if should_release:
                    _LOCK_HANDLE = None
            if should_release and active_handle is not None:
                try:
                    _unlock_file(active_handle)
                finally:
                    active_handle.close()
            elif handle is not None and not lock_acquired:
                handle.close()
