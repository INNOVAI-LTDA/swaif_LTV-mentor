from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def _configure_stores(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("USER_STORE_PATH", str(tmp_path / "users.json"))
    monkeypatch.setenv("ORG_STORE_PATH", str(tmp_path / "organizations.json"))
    monkeypatch.setenv("MENTOR_STORE_PATH", str(tmp_path / "mentors.json"))
    monkeypatch.setenv("PROTOCOL_STORE_PATH", str(tmp_path / "protocols.json"))
    monkeypatch.setenv("PILLAR_STORE_PATH", str(tmp_path / "pillars.json"))
    monkeypatch.setenv("METRIC_STORE_PATH", str(tmp_path / "metrics.json"))
    monkeypatch.setenv("STUDENT_STORE_PATH", str(tmp_path / "students.json"))
    monkeypatch.setenv("ENROLLMENT_STORE_PATH", str(tmp_path / "enrollments.json"))
    monkeypatch.setenv("MEASUREMENT_STORE_PATH", str(tmp_path / "measurements.json"))
    monkeypatch.setenv("CHECKPOINT_STORE_PATH", str(tmp_path / "checkpoints.json"))


def _login(client: TestClient) -> str:
    response = client.post(
        "/auth/login",
        json={"email": "admin@swaif.local", "password": "admin123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_smoke_e2e_full_mvp_flow(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    mentoria = client.post(
        "/admin/mentorias",
        json={"name": "Mentoria Final", "slug": "mentoria-final"},
        headers=headers,
    )
    assert mentoria.status_code == 201
    organization_id = mentoria.json()["id"]

    mentor = client.post(
        "/admin/mentores",
        json={"full_name": "Mentor Final", "email": "mentor.final@swaif.local"},
        headers=headers,
    )
    assert mentor.status_code == 201
    mentor_id = mentor.json()["id"]

    vinculo_mentor = client.post(
        f"/admin/mentorias/{organization_id}/vincular-mentor",
        json={"mentor_id": mentor_id},
        headers=headers,
    )
    assert vinculo_mentor.status_code == 200

    metodo = client.post(
        "/admin/protocolos",
        json={"organization_id": organization_id, "name": "Metodo Final", "code": "metodo-final"},
        headers=headers,
    )
    assert metodo.status_code == 201
    protocol_id = metodo.json()["id"]

    pilar = client.post(
        "/admin/pilares",
        json={
            "protocol_id": protocol_id,
            "name": "Consistencia",
            "code": "consistencia",
            "order_index": 1,
            "metadata": {"axis_sub": "Rotina"},
        },
        headers=headers,
    )
    assert pilar.status_code == 201
    pillar_id = pilar.json()["id"]

    metrica = client.post(
        "/admin/metricas",
        json={
            "protocol_id": protocol_id,
            "pillar_id": pillar_id,
            "name": "Frequencia",
            "code": "frequencia",
            "direction": "higher_better",
            "unit": "%",
        },
        headers=headers,
    )
    assert metrica.status_code == 201
    metric_id = metrica.json()["id"]

    aluno = client.post(
        "/admin/alunos",
        json={"full_name": "Aluno Final", "initials": "AF", "email": "aluno.final@swaif.local"},
        headers=headers,
    )
    assert aluno.status_code == 201
    student_id = aluno.json()["id"]

    vinculo_aluno = client.post(
        f"/admin/alunos/{student_id}/vincular-mentoria",
        json={
            "organization_id": organization_id,
            "progress_score": 0.5,
            "engagement_score": 0.7,
            "urgency_status": "watch",
            "day": 35,
            "total_days": 90,
            "days_left": 45,
            "ltv_cents": 250000,
        },
        headers=headers,
    )
    assert vinculo_aluno.status_code == 200

    carga = client.post(
        f"/admin/alunos/{student_id}/indicadores/carga-inicial",
        json={
            "metric_values": [
                {
                    "metric_id": metric_id,
                    "value_baseline": 52,
                    "value_current": 67,
                    "value_projected": 74,
                    "improving_trend": True,
                }
            ],
            "checkpoints": [
                {"week": 1, "status": "green", "label": "Onboarding"},
                {"week": 2, "status": "yellow", "label": "Ajuste de rotina"},
            ],
        },
        headers=headers,
    )
    assert carga.status_code == 200
    assert carga.json()["measurement_count"] == 1

    detalhe = client.get(f"/admin/alunos/{student_id}/detalhe", headers=headers)
    assert detalhe.status_code == 200
    assert len(detalhe.json()["metricValues"]) == 1
    assert len(detalhe.json()["checkpoints"]) == 2

    centro_lista = client.get("/admin/centro-comando/alunos", headers=headers)
    assert centro_lista.status_code == 200
    assert len(centro_lista.json()) == 1

    centro_detalhe = client.get(f"/admin/centro-comando/alunos/{student_id}", headers=headers)
    assert centro_detalhe.status_code == 200
    assert centro_detalhe.json()["id"] == student_id

    centro_timeline = client.get(
        f"/admin/centro-comando/alunos/{student_id}/timeline-anomalias",
        headers=headers,
    )
    assert centro_timeline.status_code == 200
    assert centro_timeline.json()["studentId"] == student_id

    radar = client.get(f"/admin/radar/alunos/{student_id}", headers=headers)
    assert radar.status_code == 200
    radar_body = radar.json()
    assert radar_body["studentId"] == student_id
    assert len(radar_body["axisScores"]) == 1
    assert "insight" in radar_body["axisScores"][0]

    matriz = client.get("/admin/matriz-renovacao?filter=all", headers=headers)
    assert matriz.status_code == 200
    matriz_body = matriz.json()
    assert matriz_body["filter"] == "all"
    assert len(matriz_body["items"]) == 1
    assert "kpis" in matriz_body


def test_smoke_e2e_critical_error_invalid_indicator(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    mentoria = client.post(
        "/admin/mentorias",
        json={"name": "Mentoria Erro", "slug": "mentoria-erro"},
        headers=headers,
    )
    assert mentoria.status_code == 201
    organization_id = mentoria.json()["id"]

    aluno = client.post(
        "/admin/alunos",
        json={"full_name": "Aluno Erro", "initials": "AE", "email": "aluno.erro@swaif.local"},
        headers=headers,
    )
    assert aluno.status_code == 201
    student_id = aluno.json()["id"]

    vinculo_aluno = client.post(
        f"/admin/alunos/{student_id}/vincular-mentoria",
        json={
            "organization_id": organization_id,
            "progress_score": 0.4,
            "engagement_score": 0.6,
            "day": 10,
            "total_days": 90,
            "days_left": 80,
            "ltv_cents": 100000,
        },
        headers=headers,
    )
    assert vinculo_aluno.status_code == 200

    invalid_load = client.post(
        f"/admin/alunos/{student_id}/indicadores/carga-inicial",
        json={
            "metric_values": [{"metric_id": "met_missing", "value_baseline": 10, "value_current": 12}],
            "checkpoints": [],
        },
        headers=headers,
    )
    assert invalid_load.status_code == 404
    error = invalid_load.json()["error"]
    assert error["code"] == "INDICADOR_NOT_FOUND"
