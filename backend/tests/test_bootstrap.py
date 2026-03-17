import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.storage import json_repository as json_repository_module
from app.storage.json_repository import JsonRepository


client = TestClient(app)


def test_unknown_route_returns_404() -> None:
    response = client.get("/route-that-does-not-exist")

    assert response.status_code == 404


def test_json_repository_writes_and_reads_atomically(tmp_path: Path) -> None:
    repo_file = tmp_path / "store.json"
    repo = JsonRepository(repo_file)
    payload = {"version": 1, "items": [{"id": "x1"}]}

    repo.write(payload)

    assert repo_file.exists()
    assert repo.read() == payload

    raw = json.loads(repo_file.read_text(encoding="utf-8"))
    assert raw == payload


def test_json_repository_serializes_writes_with_lock(tmp_path: Path, monkeypatch) -> None:
    repo_file = tmp_path / "store.json"
    repo = JsonRepository(repo_file)

    active_replaces = 0
    max_parallel_replaces = 0
    state_lock = threading.Lock()
    original_replace = json_repository_module.os.replace

    def delayed_replace(src, dst):
        nonlocal active_replaces, max_parallel_replaces
        with state_lock:
            active_replaces += 1
            max_parallel_replaces = max(max_parallel_replaces, active_replaces)
        time.sleep(0.01)
        original_replace(src, dst)
        with state_lock:
            active_replaces -= 1

    monkeypatch.setattr("app.storage.json_repository.os.replace", delayed_replace)

    def writer(idx: int) -> None:
        repo.write({"version": 1, "items": [{"id": f"x{idx}"}]})

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(writer, range(24)))

    assert max_parallel_replaces == 1
