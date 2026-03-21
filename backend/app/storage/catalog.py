from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from app.storage.store_registry import resolve_registered_store_paths


@dataclass(frozen=True)
class StorageTarget:
    name: str
    path: Path


def resolve_storage_targets() -> list[StorageTarget]:
    return [StorageTarget(name=name, path=path) for name, path in resolve_registered_store_paths()]


def resolve_storage_root() -> Path:
    targets = resolve_storage_targets()
    parent_paths = [target.path.parent.resolve() for target in targets]
    try:
        return Path(os.path.commonpath([str(parent) for parent in parent_paths]))
    except ValueError as exc:
        raise RuntimeError("Storage paths must share a common filesystem root.") from exc
