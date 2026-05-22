from pathlib import Path

from fastapi.testclient import TestClient


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post('/auth/login', json={'email': email, 'password': password})
    assert response.status_code == 200
    return str(response.json()['access_token'])


def test_admin_provider_view_consent_requires_fields(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv('SWAIF_STORAGE_ROOT', str(tmp_path))
    from app.main import create_app

    client = TestClient(create_app())
    token = _login(client, 'admin@swaif.local', 'admin123')
    response = client.post('/admin/provider-view/consent', json={'provider_id': '', 'provider_name': '', 'operation': '', 'consent_granted': False}, headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 422
    assert response.json()['error']['code'] == 'PROVIDER_CONSENT_INVALID'


def test_admin_provider_view_consent_logs_and_returns_payload(monkeypatch, tmp_path: Path, caplog) -> None:
    monkeypatch.setenv('SWAIF_STORAGE_ROOT', str(tmp_path))
    from app.main import create_app

    client = TestClient(create_app())
    token = _login(client, 'admin@swaif.local', 'admin123')
    with caplog.at_level('CRITICAL', logger='swaif.runtime'):
      response = client.post('/admin/provider-view/consent', json={'provider_id': 'm1', 'provider_name': 'Mentor Um', 'operation': 'evolution-radar', 'consent_granted': True}, headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    payload = response.json()
    assert payload['providerId'] == 'm1'
    assert payload['consentGranted'] is True
    assert any('admin_provider_view_edit_attempt' in record.message for record in caplog.records)
