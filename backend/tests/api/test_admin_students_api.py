from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def _configure_stores(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("USER_STORE_PATH", str(tmp_path / "users.json"))
    monkeypatch.setenv("CLIENT_STORE_PATH", str(tmp_path / "clients.json"))
    monkeypatch.setenv("ORG_STORE_PATH", str(tmp_path / "organizations.json"))
    monkeypatch.setenv("MENTOR_STORE_PATH", str(tmp_path / "mentors.json"))
    monkeypatch.setenv("PROTOCOL_STORE_PATH", str(tmp_path / "protocols.json"))
    monkeypatch.setenv("PILLAR_STORE_PATH", str(tmp_path / "pillars.json"))
    monkeypatch.setenv("METRIC_STORE_PATH", str(tmp_path / "metrics.json"))
    monkeypatch.setenv("STUDENT_STORE_PATH", str(tmp_path / "students.json"))
    monkeypatch.setenv("ENROLLMENT_STORE_PATH", str(tmp_path / "enrollments.json"))


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_admin_student_endpoints_require_auth(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.post("/admin/alunos", json={"full_name": "Aluno Sem Auth"})
    assert response.status_code == 401


def _prepare_product_and_mentor(client: TestClient, headers: dict[str, str]) -> tuple[str, str]:
    client_response = client.post(
        "/admin/clientes",
        json={"name": "Clinica Horizonte", "cnpj": "12345678000199"},
        headers=headers,
    )
    assert client_response.status_code == 201
    client_id = client_response.json()["id"]

    product_response = client.post(
        f"/admin/clientes/{client_id}/produtos",
        json={"name": "Acelerador Medico Premium", "code": "AMP-PREMIUM"},
        headers=headers,
    )
    assert product_response.status_code == 201
    product_id = product_response.json()["id"]

    mentor_response = client.post(
        f"/admin/produtos/{product_id}/mentores",
        json={"full_name": "Ana Mentora", "cpf": "12345678900", "email": "ana@swaif.local"},
        headers=headers,
    )
    assert mentor_response.status_code == 201
    return product_id, mentor_response.json()["id"]


def test_admin_can_create_link_and_list_students(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    mentoria_response = client.post(
        "/admin/mentorias",
        json={"name": "Mentoria Alunos"},
        headers=headers,
    )
    assert mentoria_response.status_code == 201
    organization_id = mentoria_response.json()["id"]

    student_response = client.post(
        "/admin/alunos",
        json={"full_name": "Aluno Teste", "initials": "AT", "email": "aluno@swaif.local"},
        headers=headers,
    )
    assert student_response.status_code == 201
    student_id = student_response.json()["id"]

    link_response = client.post(
        f"/admin/alunos/{student_id}/vincular-mentoria",
        json={
            "organization_id": organization_id,
            "progress_score": 0.4,
            "engagement_score": 0.65,
            "urgency_status": "watch",
            "day": 15,
            "total_days": 90,
            "days_left": 75,
            "ltv_cents": 180000,
        },
        headers=headers,
    )
    assert link_response.status_code == 200
    assert link_response.json()["student_id"] == student_id
    assert link_response.json()["organization_id"] == organization_id

    list_response = client.get(f"/admin/mentorias/{organization_id}/alunos", headers=headers)
    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) == 1
    assert items[0]["student"]["id"] == student_id
    assert items[0]["progress_score"] == 0.4


def test_admin_link_student_validates_ranges_and_organization(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    mentoria_response = client.post(
        "/admin/mentorias",
        json={"name": "Mentoria Delta"},
        headers=headers,
    )
    assert mentoria_response.status_code == 201
    organization_id = mentoria_response.json()["id"]

    student_response = client.post(
        "/admin/alunos",
        json={"full_name": "Aluno Delta"},
        headers=headers,
    )
    assert student_response.status_code == 201
    student_id = student_response.json()["id"]

    invalid_range = client.post(
        f"/admin/alunos/{student_id}/vincular-mentoria",
        json={
            "organization_id": organization_id,
            "progress_score": 1.2,
            "engagement_score": 0.4,
        },
        headers=headers,
    )
    assert invalid_range.status_code == 409

    missing_org = client.post(
        f"/admin/alunos/{student_id}/vincular-mentoria",
        json={
            "organization_id": "org_missing",
            "progress_score": 0.3,
            "engagement_score": 0.4,
        },
        headers=headers,
    )
    assert missing_org.status_code == 404


def test_admin_creates_and_lists_students_by_mentor(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    product_id, mentor_id = _prepare_product_and_mentor(client, headers)

    create_response = client.post(
        f"/admin/mentores/{mentor_id}/alunos",
        json={
            "full_name": "Aluno Teste",
            "cpf": "123.456.789-00",
            "email": "aluno@swaif.local",
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["mentor_id"] == mentor_id
    assert created["organization_id"] == product_id

    mentor_list = client.get(f"/admin/mentores/{mentor_id}/alunos", headers=headers)
    assert mentor_list.status_code == 200
    assert len(mentor_list.json()) == 1
    assert mentor_list.json()[0]["full_name"] == "Aluno Teste"

    product_list = client.get(f"/admin/produtos/{product_id}/alunos", headers=headers)
    assert product_list.status_code == 200
    assert len(product_list.json()) == 1
    assert product_list.json()[0]["mentor_id"] == mentor_id


def test_admin_student_create_rejects_duplicate_cpf(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    _, mentor_id = _prepare_product_and_mentor(client, headers)

    first = client.post(
        f"/admin/mentores/{mentor_id}/alunos",
        json={"full_name": "Aluno Um", "cpf": "12345678900", "email": "aluno1@swaif.local"},
        headers=headers,
    )
    assert first.status_code == 201

    duplicate = client.post(
        f"/admin/mentores/{mentor_id}/alunos",
        json={"full_name": "Aluno Dois", "cpf": "123.456.789-00", "email": "aluno2@swaif.local"},
        headers=headers,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "ALUNO_CONFLICT"
