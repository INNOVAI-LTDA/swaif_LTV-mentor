from pathlib import Path

from fastapi.testclient import TestClient


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post('/auth/login', json={'email': email, 'password': password})
    assert response.status_code == 200
    return str(response.json()['access_token'])


def test_catalog_requires_admin_role(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv('SWAIF_STORAGE_ROOT', str(tmp_path))
    from app.main import create_app

    client = TestClient(create_app())
    provider_token = _login(client, 'mentor@swaif.local', 'mentor123')
    response = client.get('/admin/api-operations/catalog', headers={'Authorization': f'Bearer {provider_token}'})
    assert response.status_code == 403
    assert response.json()['error']['code'] == 'AUTH_FORBIDDEN'


def test_admin_executes_operation_and_emits_critical_log(monkeypatch, tmp_path: Path, caplog) -> None:
    monkeypatch.setenv('SWAIF_STORAGE_ROOT', str(tmp_path))
    from app.main import create_app

    client = TestClient(create_app())
    admin_token = _login(client, 'admin@swaif.local', 'admin123')

    catalog = client.get('/admin/api-operations/catalog', headers={'Authorization': f'Bearer {admin_token}'})
    assert catalog.status_code == 200
    endpoint = catalog.json()['items'][0]['endpoint']

    with caplog.at_level('CRITICAL', logger='swaif.runtime'):
        response = client.post('/admin/api-operations/execute', json={'endpoint': endpoint}, headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'success'
    assert payload['requestedBy'] == 'admin@swaif.local'
    assert payload['endpoint'] == endpoint
    assert any('admin_api_operation_requested urgency=critical' in record.message for record in caplog.records)
