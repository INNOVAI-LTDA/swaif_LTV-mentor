from __future__ import annotations

import json
import os
import shutil
import tempfile
import threading
from pathlib import Path
from typing import Any

from app.storage.io_gate import hold_storage_io_lock


class JsonRepository:
    _locks_by_file: dict[str, threading.RLock] = {}
    _locks_guard = threading.Lock()

    def __init__(self, file_path: str | Path) -> None:
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = self._get_lock(self.file_path.resolve())

    @classmethod
    def _get_lock(cls, file_path: Path) -> threading.RLock:
        key = str(file_path)
        with cls._locks_guard:
            existing = cls._locks_by_file.get(key)
            if existing is not None:
                return existing
            created = threading.RLock()
            cls._locks_by_file[key] = created
            return created

    def read(self) -> dict[str, Any]:
        with self._lock:
            if not self.file_path.exists():
                return self.default_payload()

            with self.file_path.open("r", encoding="utf-8") as fh:
                return json.load(fh)

    @staticmethod
    def default_payload() -> dict[str, Any]:
        return {"version": 1, "items": []}

    @staticmethod
    def validate_snapshot_payload(payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise RuntimeError("Backup snapshot must contain a JSON object payload.")

        version = payload.get("version")
        items = payload.get("items")

        if not isinstance(version, int) or version < 1:
            raise RuntimeError("Backup snapshot payload must contain an integer version >= 1.")
        if not isinstance(items, list):
            raise RuntimeError("Backup snapshot payload must contain an items list.")

        return payload

    @classmethod
    def load_snapshot_payload(cls, source: str | Path) -> dict[str, Any]:
        source_path = Path(source)
        with source_path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
        return cls.validate_snapshot_payload(payload)

    def write(self, data: dict[str, Any]) -> None:
        with hold_storage_io_lock():
            with self._lock:
                self.file_path.parent.mkdir(parents=True, exist_ok=True)

                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=self.file_path.parent,
                    delete=False,
                ) as tmp:
                    json.dump(data, tmp, ensure_ascii=False, indent=2)
                    tmp_path = Path(tmp.name)

                os.replace(tmp_path, self.file_path)

    def snapshot_to(self, destination: str | Path) -> Path:
        target_path = Path(destination)
        with hold_storage_io_lock():
            with self._lock:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                if not self.file_path.exists():
                    target_path.write_text(
                        json.dumps(self.default_payload(), ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                    return target_path

                shutil.copy2(self.file_path, target_path)
                return target_path

    def restore_from(self, source: str | Path) -> None:
        payload = self.load_snapshot_payload(source)
        self.write(payload)
