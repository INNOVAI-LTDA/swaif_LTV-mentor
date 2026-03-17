from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def _configure_stores(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("USER_STORE_PATH", str(tmp_path / "users.json"))
    monkeypatch.setenv("CLIENT_STORE_PATH", str(tmp_path / "clients.json"))
    monkeypatch.setenv("ORG_STORE_PATH", str(tmp_path / "organizations.json"))
    monkeypatch.setenv("MENTOR_STORE_PATH", str(tmp_path / "mentors.json"))
    monkeypatch.setenv("STUDENT_STORE_PATH", str(tmp_path / "students.json"))
    monkeypatch.setenv("ENROLLMENT_STORE_PATH", str(tmp_path / "enrollments.json"))


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _prepare_product_mentor_student(client: TestClient, headers: dict[str, str]) -> tuple[str, str, str, str]:
    client_response = client.post("/admin/clientes", json={"name": "Clinica Horizonte", "cnpj": "12345678000199"}, headers=headers)
    client_id = client_response.json()["id"]
    product_response = client.post(
        f"/admin/clientes/{client_id}/produtos",
        json={"name": "Acelerador Medico Premium", "code": "AMP-PREMIUM"},
        headers=headers,
    )
    product_id = product_response.json()["id"]
    mentor_a = client.post(
        f"/admin/produtos/{product_id}/mentores",
        json={"full_name": "Ana Mentora", "cpf": "12345678900", "email": "ana@swaif.local"},
        headers=headers,
    ).json()["id"]
    mentor_b = client.post(
        f"/admin/produtos/{product_id}/mentores",
        json={"full_name": "Bea Mentora", "cpf": "12345678901", "email": "bea@swaif.local"},
        headers=headers,
    ).json()["id"]
    student = client.post(
        f"/admin/mentores/{mentor_a}/alunos",
        json={"full_name": "Aluno Teste", "cpf": "12345678902", "email": "aluno@swaif.local"},
        headers=headers,
    ).json()["id"]
    return product_id, mentor_a, mentor_b, student


def test_admin_student_link_endpoints_require_auth(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.post("/admin/alunos/std_1/reatribuir-mentor", json={"target_mentor_id": "mtr_2", "justificativa": "Mover"})
    assert response.status_code == 401


def test_admin_reassigns_student_between_mentors(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_login(client, 'admin@swaif.local', 'admin123')}"}

    product_id, mentor_a, mentor_b, student_id = _prepare_product_mentor_student(client, headers)

    response = client.post(
        f"/admin/alunos/{student_id}/reatribuir-mentor",
        json={"target_mentor_id": mentor_b, "justificativa": "Redistribuicao operacional"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["mentor_id"] == mentor_b

    mentor_a_students = client.get(f"/admin/mentores/{mentor_a}/alunos", headers=headers)
    assert mentor_a_students.status_code == 200
    assert mentor_a_students.json() == []

    mentor_b_students = client.get(f"/admin/mentores/{mentor_b}/alunos", headers=headers)
    assert mentor_b_students.status_code == 200
    assert len(mentor_b_students.json()) == 1

    product_students = client.get(f"/admin/produtos/{product_id}/alunos", headers=headers)
    assert product_students.status_code == 200
    assert len(product_students.json()) == 1
    assert product_students.json()[0]["mentor_id"] == mentor_b


def test_admin_unlinks_student_logically(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_login(client, 'admin@swaif.local', 'admin123')}"}

    _, mentor_a, _, student_id = _prepare_product_mentor_student(client, headers)

    response = client.post(
        f"/admin/alunos/{student_id}/desvincular",
        json={"justificativa": "Aluno pausado"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert response.json()["deactivated_reason"] == "Aluno pausado"

    mentor_students = client.get(f"/admin/mentores/{mentor_a}/alunos", headers=headers)
    assert mentor_students.status_code == 200
    assert mentor_students.json() == []


def test_admin_student_link_requires_justification(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {_login(client, 'admin@swaif.local', 'admin123')}"}

    _, _, mentor_b, student_id = _prepare_product_mentor_student(client, headers)

    response = client.post(
        f"/admin/alunos/{student_id}/reatribuir-mentor",
        json={"target_mentor_id": mentor_b, "justificativa": " "},
        headers=headers,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VINCULO_INVALIDO"
