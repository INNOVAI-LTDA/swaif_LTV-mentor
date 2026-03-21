import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from app.operations import storage_maintenance
from app.operations.storage_maintenance import (
    create_backup_snapshot,
    restore_backup_snapshot,
    verify_backup_snapshot,
)
from app.storage.client_repository import ClientRepository
from app.storage.io_gate import hold_storage_io_lock, storage_io_lock_path
from app.storage.json_repository import JsonRepository


STORE_ENVIRONMENTS = {
    "USER_STORE_PATH": "users.json",
    "CLIENT_STORE_PATH": "clients.json",
    "ORG_STORE_PATH": "organizations.json",
    "MENTOR_STORE_PATH": "mentors.json",
    "PROTOCOL_STORE_PATH": "protocols.json",
    "PILLAR_STORE_PATH": "pillars.json",
    "METRIC_STORE_PATH": "metrics.json",
    "STUDENT_STORE_PATH": "students.json",
    "ENROLLMENT_STORE_PATH": "enrollments.json",
    "MEASUREMENT_STORE_PATH": "measurements.json",
    "CHECKPOINT_STORE_PATH": "checkpoints.json",
}


def _configure_store_paths(monkeypatch, tmp_path: Path) -> dict[str, Path]:
    data_dir = tmp_path / "data"
    configured: dict[str, Path] = {}
    for env_name, file_name in STORE_ENVIRONMENTS.items():
        path = data_dir / file_name
        monkeypatch.setenv(env_name, str(path))
        configured[env_name] = path
    monkeypatch.setenv("STORAGE_BACKUP_DIR", str(tmp_path / "backups"))
    return configured


def test_backup_snapshot_captures_all_store_files_and_can_restore(monkeypatch, tmp_path: Path) -> None:
    configured_paths = _configure_store_paths(monkeypatch, tmp_path)
    clients_path = configured_paths["CLIENT_STORE_PATH"]

    clients = ClientRepository()
    first_client = clients.create(name="Clinica Norte", cnpj="11", slug="clinica-norte")
    original_clients_payload = JsonRepository(clients_path).read()

    snapshot_dir = create_backup_snapshot()
    manifest = verify_backup_snapshot(snapshot_dir)
    assert len(manifest["stores"]) == len(STORE_ENVIRONMENTS)

    clients.create(name="Clinica Sul", cnpj="22", slug="clinica-sul")
    assert len(JsonRepository(clients_path).read()["items"]) == 2

    restore_result = restore_backup_snapshot(snapshot_dir)
    assert "clients" in restore_result["stores_restored"]
    assert restore_result["rollback_snapshot_dir"] is not None
    restored_payload = JsonRepository(clients_path).read()
    assert restored_payload == original_clients_payload
    assert restored_payload["items"][0]["id"] == first_client["id"]


def test_backup_snapshot_uses_unique_directory_when_timestamp_collides(monkeypatch, tmp_path: Path) -> None:
    _configure_store_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(storage_maintenance, "_snapshot_id", lambda: "20260319T120000Z")

    first = create_backup_snapshot()
    second = create_backup_snapshot()

    assert first != second
    assert first.exists()
    assert second.exists()


def test_backup_snapshot_retries_when_collision_directory_already_exists(monkeypatch, tmp_path: Path) -> None:
    _configure_store_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(storage_maintenance, "_snapshot_id", lambda: "20260319T120000Z")

    backup_dir = tmp_path / "backups"
    (backup_dir / "snapshot-20260319T120000Z").mkdir(parents=True, exist_ok=True)
    (backup_dir / "snapshot-20260319T120000Z-aaaaaa").mkdir(parents=True, exist_ok=True)

    uuids = iter(["aaaaaa111111", "bbbbbb222222"])
    monkeypatch.setattr(
        storage_maintenance,
        "uuid4",
        lambda: type("StableUuid", (), {"hex": next(uuids)})(),
    )

    snapshot_dir = create_backup_snapshot()

    assert snapshot_dir.name == "snapshot-20260319T120000Z-bbbbbb"
    assert snapshot_dir.exists()


def test_verify_backup_snapshot_requires_manifest(tmp_path: Path) -> None:
    snapshot_dir = tmp_path / "snapshot-without-manifest"
    snapshot_dir.mkdir(parents=True)

    try:
        verify_backup_snapshot(snapshot_dir)
    except RuntimeError as error:
        assert str(error) == "Backup snapshot is missing manifest.json."
    else:
        raise AssertionError("Expected missing manifest to fail.")


def test_verify_backup_snapshot_rejects_incomplete_manifest(monkeypatch, tmp_path: Path) -> None:
    _configure_store_paths(monkeypatch, tmp_path)
    snapshot_dir = create_backup_snapshot()
    manifest_path = snapshot_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["stores"] = manifest["stores"][:-1]
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    try:
        verify_backup_snapshot(snapshot_dir)
    except RuntimeError as error:
        assert "Backup snapshot manifest is incomplete." in str(error)
    else:
        raise AssertionError("Expected incomplete manifest to fail.")


def test_verify_backup_snapshot_rejects_invalid_store_payload(monkeypatch, tmp_path: Path) -> None:
    _configure_store_paths(monkeypatch, tmp_path)
    snapshot_dir = create_backup_snapshot()
    (snapshot_dir / "clients.json").write_text(json.dumps({"version": 1}), encoding="utf-8")

    try:
        verify_backup_snapshot(snapshot_dir)
    except RuntimeError as error:
        assert "clients.json" in str(error)
        assert "items list" in str(error)
    else:
        raise AssertionError("Expected invalid snapshot payload to fail verification.")


def test_restore_backup_snapshot_rolls_back_when_restore_fails(monkeypatch, tmp_path: Path) -> None:
    configured_paths = _configure_store_paths(monkeypatch, tmp_path)
    clients_path = configured_paths["CLIENT_STORE_PATH"]
    metrics_path = configured_paths["METRIC_STORE_PATH"]

    clients = ClientRepository()
    clients.create(name="Clinica Norte", cnpj="11", slug="clinica-norte")
    JsonRepository(metrics_path).write({"version": 1, "items": [{"id": "metric-a"}]})

    snapshot_dir = create_backup_snapshot()

    clients.create(name="Clinica Sul", cnpj="22", slug="clinica-sul")
    JsonRepository(metrics_path).write({"version": 1, "items": [{"id": "metric-b"}]})
    mutated_clients_payload = JsonRepository(clients_path).read()
    mutated_metrics_payload = JsonRepository(metrics_path).read()

    original_write = JsonRepository.write
    failure_count = 0

    def fail_on_metrics(self: JsonRepository, payload: dict[str, object]) -> None:
        nonlocal failure_count
        if Path(self.file_path).name == "metrics.json":
            if failure_count == 0:
                failure_count += 1
                raise RuntimeError("Simulated restore failure.")
        original_write(self, payload)

    monkeypatch.setattr(JsonRepository, "write", fail_on_metrics)

    try:
        restore_backup_snapshot(snapshot_dir)
    except RuntimeError as error:
        assert str(error) == "Simulated restore failure."
    else:
        raise AssertionError("Expected restore failure.")

    assert JsonRepository(clients_path).read() == mutated_clients_payload
    assert JsonRepository(metrics_path).read() == mutated_metrics_payload


def test_storage_io_lock_blocks_cross_process_writes(monkeypatch, tmp_path: Path) -> None:
    configured_paths = _configure_store_paths(monkeypatch, tmp_path)
    clients_path = configured_paths["CLIENT_STORE_PATH"]
    alternate_backup_dir = tmp_path / "other-backups"

    script = (
        "import os\n"
        f"os.environ['STORAGE_BACKUP_DIR'] = r'{alternate_backup_dir}'\n"
        "from app.storage.json_repository import JsonRepository\n"
        f"JsonRepository(r'{clients_path}').write({{'version': 1, 'items': [{{'id': 'client-1'}}]}})\n"
        "print('done')\n"
    )
    backend_dir = Path(__file__).resolve().parents[1]

    with hold_storage_io_lock():
        started_at = time.monotonic()
        process = subprocess.Popen(
            [sys.executable, "-c", script],
            cwd=str(backend_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        time.sleep(0.3)
        assert process.poll() is None

    stdout, stderr = process.communicate(timeout=10)
    assert process.returncode == 0, stderr
    assert "done" in stdout
    assert time.monotonic() - started_at >= 0.3
    assert JsonRepository(clients_path).read()["items"][0]["id"] == "client-1"


def test_storage_io_lock_path_uses_writable_temp_location_for_split_store_layout(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("USER_STORE_PATH", str(tmp_path / "app-data" / "users.json"))
    monkeypatch.setenv("CLIENT_STORE_PATH", str(tmp_path / "client-data" / "clients.json"))
    monkeypatch.setenv("ORG_STORE_PATH", str(tmp_path / "org-data" / "organizations.json"))
    monkeypatch.setenv("MENTOR_STORE_PATH", str(tmp_path / "mentor-data" / "mentors.json"))
    monkeypatch.setenv("PROTOCOL_STORE_PATH", str(tmp_path / "protocol-data" / "protocols.json"))
    monkeypatch.setenv("PILLAR_STORE_PATH", str(tmp_path / "pillar-data" / "pillars.json"))
    monkeypatch.setenv("METRIC_STORE_PATH", str(tmp_path / "metric-data" / "metrics.json"))
    monkeypatch.setenv("STUDENT_STORE_PATH", str(tmp_path / "student-data" / "students.json"))
    monkeypatch.setenv("ENROLLMENT_STORE_PATH", str(tmp_path / "enrollment-data" / "enrollments.json"))
    monkeypatch.setenv("MEASUREMENT_STORE_PATH", str(tmp_path / "measurement-data" / "measurements.json"))
    monkeypatch.setenv("CHECKPOINT_STORE_PATH", str(tmp_path / "checkpoint-data" / "checkpoints.json"))
    monkeypatch.setenv("STORAGE_BACKUP_DIR", str(tmp_path / "backups-a"))

    first_lock_path = storage_io_lock_path()
    monkeypatch.setenv("STORAGE_BACKUP_DIR", str(tmp_path / "backups-b"))
    second_lock_path = storage_io_lock_path()

    expected_parent = Path(tempfile.gettempdir()) / "swaif-storage-locks"

    assert first_lock_path.parent == expected_parent
    assert second_lock_path.parent == expected_parent
    assert first_lock_path == second_lock_path
    assert first_lock_path.name.endswith(".storage-io.lock")


def test_restore_backup_snapshot_wraps_rollback_verification_failure(monkeypatch, tmp_path: Path) -> None:
    _configure_store_paths(monkeypatch, tmp_path)
    snapshot_dir = create_backup_snapshot()

    original_verify = storage_maintenance.verify_backup_snapshot

    def fail_live_restore(*args, **kwargs):
        raise RuntimeError("Simulated live restore failure.")

    def fail_rollback_verify(snapshot_path):
        if Path(snapshot_path).name.startswith("pre-restore-"):
            raise RuntimeError("Rollback snapshot manifest is corrupt.")
        return original_verify(snapshot_path)

    monkeypatch.setattr(storage_maintenance, "_build_restore_plan", fail_live_restore)
    monkeypatch.setattr(storage_maintenance, "verify_backup_snapshot", fail_rollback_verify)

    try:
        restore_backup_snapshot(snapshot_dir)
    except RuntimeError as error:
        message = str(error)
        assert "Manual operator intervention is required." in message
        assert "Rollback snapshot manifest is corrupt." in message
        assert "pre-restore-" in message
    else:
        raise AssertionError("Expected rollback verification failure to be wrapped.")


def test_backup_snapshot_manifest_is_json(tmp_path: Path, monkeypatch) -> None:
    _configure_store_paths(monkeypatch, tmp_path)

    snapshot_dir = create_backup_snapshot()
    manifest = json.loads((snapshot_dir / "manifest.json").read_text(encoding="utf-8"))

    assert isinstance(manifest["stores"], list)
    assert manifest["snapshot_dir"] == str(snapshot_dir.resolve())
