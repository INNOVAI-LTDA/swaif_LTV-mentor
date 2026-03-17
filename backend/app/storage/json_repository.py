from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any


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
                return {"version": 1, "items": []}

            with self.file_path.open("r", encoding="utf-8") as fh:
                return json.load(fh)

    def write(self, data: dict[str, Any]) -> None:
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
