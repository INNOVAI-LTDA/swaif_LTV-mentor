from __future__ import annotations

import argparse
import json
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.config.runtime import get_storage_backup_dir
from app.storage.catalog import resolve_storage_root, resolve_storage_targets
from app.storage.io_gate import hold_storage_io_lock
from app.storage.json_repository import JsonRepository


def _snapshot_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _manifest_path(snapshot_dir: Path) -> Path:
    return snapshot_dir / "manifest.json"


def _expected_store_map() -> dict[str, Path]:
    return {target.name: target.path.resolve() for target in resolve_storage_targets()}


def _create_snapshot_dir(base_dir: Path, *, prefix: str) -> Path:
    snapshot_id = _snapshot_id()
    base_dir.mkdir(parents=True, exist_ok=True)

    for attempt in range(32):
        suffix = "" if attempt == 0 else f"-{uuid4().hex[:6]}"
        candidate = base_dir / f"{prefix}-{snapshot_id}{suffix}"
        try:
            candidate.mkdir(parents=True, exist_ok=False)
            return candidate
        except FileExistsError:
            continue

    raise RuntimeError(f"Could not allocate a unique snapshot directory under {base_dir}.")


def _capture_snapshot(snapshot_dir: Path) -> list[dict[str, Any]]:
    stores: list[dict[str, Any]] = []
    for target in resolve_storage_targets():
        snapshot_path = snapshot_dir / target.path.name
        JsonRepository(target.path).snapshot_to(snapshot_path)
        stores.append(
            {
                "name": target.name,
                "source_path": str(target.path.resolve()),
                "snapshot_file": snapshot_path.name,
                "size_bytes": snapshot_path.stat().st_size,
            }
        )
    return stores


def create_backup_snapshot(
    destination_root: str | Path | None = None,
    *,
    prefix: str = "snapshot",
    _assume_storage_lock: bool = False,
) -> Path:
    base_dir = Path(destination_root) if destination_root is not None else get_storage_backup_dir()
    lock_context = hold_storage_io_lock() if not _assume_storage_lock else nullcontext()
    with lock_context:
        snapshot_dir = _create_snapshot_dir(base_dir, prefix=prefix)
        stores = _capture_snapshot(snapshot_dir)

        manifest = {
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "storage_root": str(resolve_storage_root()),
            "snapshot_dir": str(snapshot_dir.resolve()),
            "stores": stores,
        }
        _manifest_path(snapshot_dir).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return snapshot_dir


def verify_backup_snapshot(snapshot_dir: str | Path) -> dict[str, Any]:
    snapshot_path = Path(snapshot_dir)
    manifest_file = _manifest_path(snapshot_path)
    if not manifest_file.exists():
        raise RuntimeError("Backup snapshot is missing manifest.json.")

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    stores = manifest.get("stores")
    if not isinstance(stores, list) or not stores:
        raise RuntimeError("Backup snapshot manifest must list at least one store.")

    expected_store_map = _expected_store_map()
    expected_names = set(expected_store_map)
    seen_names: set[str] = set()

    for store in stores:
        if not isinstance(store, dict):
            raise RuntimeError("Backup snapshot manifest contains an invalid store entry.")

        name = store.get("name")
        snapshot_name = store.get("snapshot_file")
        source_path = store.get("source_path")
        size_bytes = store.get("size_bytes")

        if not isinstance(name, str) or not name:
            raise RuntimeError("Backup snapshot manifest contains a store without name.")
        if name not in expected_names:
            raise RuntimeError(f"Backup snapshot manifest references an unknown store: {name}")
        if name in seen_names:
            raise RuntimeError(f"Backup snapshot manifest contains a duplicate store entry: {name}")
        seen_names.add(name)

        if not isinstance(snapshot_name, str) or not snapshot_name:
            raise RuntimeError("Backup snapshot manifest contains a store without snapshot_file.")
        if Path(snapshot_name).name != snapshot_name:
            raise RuntimeError("Backup snapshot manifest snapshot_file must be a bare filename.")
        if not isinstance(source_path, str) or not source_path:
            raise RuntimeError(f"Backup snapshot manifest store entry is missing source_path: {name}")
        if not isinstance(size_bytes, int) or size_bytes < 0:
            raise RuntimeError(f"Backup snapshot manifest store entry has invalid size_bytes: {name}")

        snapshot_file = snapshot_path / snapshot_name
        if not snapshot_file.exists():
            raise RuntimeError(f"Backup snapshot is missing store file: {snapshot_name}")
        try:
            JsonRepository.load_snapshot_payload(snapshot_file)
        except RuntimeError as exc:
            raise RuntimeError(f"Backup snapshot store file is invalid: {snapshot_name}. {exc}") from exc

    if seen_names != expected_names:
        missing_names = sorted(expected_names - seen_names)
        raise RuntimeError(f"Backup snapshot manifest is incomplete. Missing stores: {', '.join(missing_names)}")

    return manifest


def _build_restore_plan(manifest: dict[str, Any], snapshot_path: Path) -> list[tuple[str, Path, dict[str, Any]]]:
    targets_by_name = _expected_store_map()
    restore_plan: list[tuple[str, Path, dict[str, Any]]] = []
    for store in manifest["stores"]:
        name = store["name"]
        target_path = targets_by_name.get(name)
        if target_path is None:
            raise RuntimeError(f"Backup snapshot references unknown store: {name}")
        payload = JsonRepository.load_snapshot_payload(snapshot_path / store["snapshot_file"])
        restore_plan.append((name, target_path, payload))
    return restore_plan


def _apply_restore_plan(restore_plan: list[tuple[str, Path, dict[str, Any]]]) -> list[str]:
    restored_names: list[str] = []
    for name, target_path, payload in restore_plan:
        JsonRepository(target_path).write(payload)
        restored_names.append(name)
    return restored_names


def restore_backup_snapshot(
    snapshot_dir: str | Path,
    *,
    create_rollback_snapshot: bool = True,
) -> dict[str, Any]:
    manifest = verify_backup_snapshot(snapshot_dir)
    snapshot_path = Path(snapshot_dir)

    with hold_storage_io_lock():
        rollback_snapshot_dir: Path | None = None
        if create_rollback_snapshot:
            rollback_snapshot_dir = create_backup_snapshot(prefix="pre-restore", _assume_storage_lock=True)

        try:
            restore_plan = _build_restore_plan(manifest, snapshot_path)
            restored_names = _apply_restore_plan(restore_plan)
        except Exception as exc:
            if rollback_snapshot_dir is not None:
                try:
                    rollback_manifest = verify_backup_snapshot(rollback_snapshot_dir)
                    rollback_plan = _build_restore_plan(rollback_manifest, rollback_snapshot_dir)
                    _apply_restore_plan(rollback_plan)
                except Exception as rollback_exc:
                    raise RuntimeError(
                        "Restore failed and rollback could not fully recover the pre-restore snapshot. "
                        f"Manual operator intervention is required. Rollback snapshot: {rollback_snapshot_dir}. "
                        f"Rollback error: {rollback_exc}"
                    ) from exc
            raise

        return {
            "restored_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "snapshot_dir": str(snapshot_path.resolve()),
            "stores_restored": restored_names,
            "rollback_snapshot_dir": str(rollback_snapshot_dir.resolve()) if rollback_snapshot_dir else None,
        }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage JSON storage snapshots for local production validation.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    backup_parser = subparsers.add_parser("backup", help="Create a snapshot of all JSON stores.")
    backup_parser.add_argument("--output-dir", dest="output_dir")

    verify_parser = subparsers.add_parser("verify", help="Verify a snapshot manifest and store files.")
    verify_parser.add_argument("snapshot_dir")

    restore_parser = subparsers.add_parser("restore", help="Restore all JSON stores from a snapshot.")
    restore_parser.add_argument("snapshot_dir")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "backup":
        snapshot_dir = create_backup_snapshot(destination_root=args.output_dir)
        print(json.dumps({"snapshot_dir": str(snapshot_dir.resolve())}, indent=2))
        return 0

    if args.command == "verify":
        manifest = verify_backup_snapshot(args.snapshot_dir)
        print(json.dumps(manifest, indent=2))
        return 0

    if args.command == "restore":
        result = restore_backup_snapshot(args.snapshot_dir)
        print(json.dumps(result, indent=2))
        return 0

    parser.error("Unknown command.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
