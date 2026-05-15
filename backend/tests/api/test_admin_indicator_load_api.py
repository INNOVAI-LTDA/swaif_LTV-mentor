from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.api.routes.admin_students import get_indicator_carga_service
from app.services.indicator_carga_service import IndicatorCargaService
from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.measurement_overall_repository import MeasurementOverallRepository
from app.storage.metric_repository import MetricRepository
from app.storage.organization_repository import OrganizationRepository
from app.storage.pillar_repository import PillarRepository
from app.storage.product_assignment_repository import ProductAssignmentRepository
from app.storage.student_repository import StudentRepository


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


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _assert_v1_error_envelope(
    response,
    *,
    status_code: int,
    expected_code: str,
    expected_message: str,
) -> None:
    assert response.status_code == status_code
    body = response.json()
    assert "error" in body
    error = body["error"]
    assert error["status"] == status_code
    assert error["code"] == expected_code
    assert error["message"] == expected_message
    assert "details" in error


def _prepare_student_and_metric(client: TestClient, headers: dict[str, str]) -> tuple[str, str]:
    mentoria_response = client.post("/admin/mentorias", json={"name": "Mentoria Indicadores"}, headers=headers)
    assert mentoria_response.status_code == 201
    organization_id = mentoria_response.json()["id"]

    student_response = client.post("/admin/alunos", json={"full_name": "Aluno Indicadores"}, headers=headers)
    assert student_response.status_code == 201
    student_id = student_response.json()["id"]

    link_response = client.post(
        f"/admin/alunos/{student_id}/vincular-mentoria",
        json={"organization_id": organization_id, "progress_score": 0.35, "engagement_score": 0.6},
        headers=headers,
    )
    assert link_response.status_code == 200

    protocol_response = client.post(
        "/admin/protocolos",
        json={"organization_id": organization_id, "name": "Metodo Indicadores"},
        headers=headers,
    )
    assert protocol_response.status_code == 201
    protocol_id = protocol_response.json()["id"]

    pillar_response = client.post(
        "/admin/pilares",
        json={"protocol_id": protocol_id, "name": "Compromisso"},
        headers=headers,
    )
    assert pillar_response.status_code == 201
    pillar_id = pillar_response.json()["id"]

    metric_response = client.post(
        "/admin/metricas",
        json={"protocol_id": protocol_id, "pillar_id": pillar_id, "name": "Frequencia", "unit": "%"},
        headers=headers,
    )
    assert metric_response.status_code == 201
    return student_id, metric_response.json()["id"]


class _MemoryMeasurementRepository:
    runtime_backend = "postgres"

    def __init__(self) -> None:
        self.items: list[dict] = []

    def replace_for_enrollment(self, enrollment_id: str, rows: list[dict]) -> list[dict]:
        self.items = [item for item in self.items if item.get("enrollment_id") != enrollment_id]
        created: list[dict] = []
        for index, row in enumerate(rows):
            created.append(
                {
                    "id": f"mea_{index+1}",
                    "enrollment_id": enrollment_id,
                    "metric_id": str(row["metric_id"]),
                    "value_baseline": float(row["value_baseline"]),
                    "value_current": float(row["value_current"]),
                    "value_projected": row.get("value_projected"),
                    "improving_trend": row.get("improving_trend"),
                }
            )
        self.items.extend(created)
        return created

    def list_measurements(self) -> list[dict]:
        return list(self.items)


class _MemoryCheckpointRepository:
    runtime_backend = "postgres"

    def __init__(self) -> None:
        self.items: list[dict] = []

    def replace_for_enrollment(self, enrollment_id: str, rows: list[dict]) -> list[dict]:
        self.items = [item for item in self.items if item.get("enrollment_id") != enrollment_id]
        created: list[dict] = []
        for index, row in enumerate(rows):
            created.append(
                {
                    "id": f"chk_{index+1}",
                    "enrollment_id": enrollment_id,
                    "week": int(row["week"]),
                    "status": str(row["status"]),
                    "label": row.get("label"),
                }
            )
        self.items.extend(created)
        return created

    def list_by_enrollment(self, enrollment_id: str) -> list[dict]:
        return [item for item in self.items if item.get("enrollment_id") == enrollment_id]


class _JsonBackendMeasurementRepository(_MemoryMeasurementRepository):
    runtime_backend = "json"


class _JsonBackendCheckpointRepository(_MemoryCheckpointRepository):
    runtime_backend = "json"


def _override_indicator_service_with_repositories(
    *,
    measurements,
    checkpoints,
) -> None:
    def _service() -> IndicatorCargaService:
        return IndicatorCargaService(
            students=StudentRepository(),
            organizations=OrganizationRepository(),
            enrollments=EnrollmentRepository(),
            product_assignments=ProductAssignmentRepository(),
            metrics=MetricRepository(),
            measurements=measurements,
            checkpoints=checkpoints,
            pillars=PillarRepository(),
            measurement_overalls=MeasurementOverallRepository(),
        )

    app.dependency_overrides[get_indicator_carga_service] = _service


def test_indicator_load_requires_auth(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.post(
        "/admin/alunos/std_1/indicadores/carga-inicial",
        json={"metric_values": [], "checkpoints": []},
    )
    assert response.status_code == 401


def test_admin_can_load_initial_indicators_and_read_student_detail(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://runtime-db")
    _override_indicator_service_with_repositories(
        measurements=_MemoryMeasurementRepository(),
        checkpoints=_MemoryCheckpointRepository(),
    )
    client = TestClient(app)
    try:
        admin_token = _login(client, "admin@swaif.local", "admin123")
        headers = {"Authorization": f"Bearer {admin_token}"}

        student_id, metric_id = _prepare_student_and_metric(client, headers)

        load_response = client.post(
            f"/admin/alunos/{student_id}/indicadores/carga-inicial",
            json={
                "metric_values": [
                    {"metric_id": metric_id, "value_baseline": 55, "value_current": 68, "value_projected": 75, "improving_trend": True}
                ],
                "checkpoints": [
                    {"week": 1, "status": "green", "label": "Inicio consistente"},
                    {"week": 2, "status": "yellow", "label": "Ajustar rotina"},
                ],
            },
            headers=headers,
        )
        assert load_response.status_code == 200
        assert load_response.json()["measurement_count"] == 1
        assert load_response.json()["checkpoint_count"] == 2

        detail_response = client.get(f"/admin/alunos/{student_id}/detalhe", headers=headers)
        assert detail_response.status_code == 200
        detail = detail_response.json()
        assert detail["id"] == student_id
        assert len(detail["metricValues"]) == 1
        assert detail["metricValues"][0]["valueCurrent"] == 68
        assert len(detail["checkpoints"]) == 2
    finally:
        app.dependency_overrides.pop(get_indicator_carga_service, None)


def test_indicator_load_rejects_non_registered_metric(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://runtime-db")
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    student_id, _ = _prepare_student_and_metric(client, headers)

    load_response = client.post(
        f"/admin/alunos/{student_id}/indicadores/carga-inicial",
        json={
            "metric_values": [{"metric_id": "met_missing", "value_baseline": 10, "value_current": 15}],
            "checkpoints": [],
        },
        headers=headers,
    )
    assert load_response.status_code == 404


def test_indicator_load_rejects_inactive_metric(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://runtime-db")
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    student_id, metric_id = _prepare_student_and_metric(client, headers)

    metric_store = tmp_path / "metrics.json"
    content = metric_store.read_text(encoding="utf-8")
    metric_store.write_text(content.replace('"is_active": true', '"is_active": false', 1), encoding="utf-8")

    load_response = client.post(
        f"/admin/alunos/{student_id}/indicadores/carga-inicial",
        json={
            "metric_values": [{"metric_id": metric_id, "value_baseline": 10, "value_current": 15}],
            "checkpoints": [],
        },
        headers=headers,
    )
    assert load_response.status_code == 404


def test_indicator_load_returns_postgres_runtime_unavailable_in_production_like(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
    client = TestClient(app)
    admin_token = _login(client, "admin@swaif.local", "admin123")
    headers = {"Authorization": f"Bearer {admin_token}"}

    student_id, metric_id = _prepare_student_and_metric(client, headers)
    load_response = client.post(
        f"/admin/alunos/{student_id}/indicadores/carga-inicial",
        json={
            "metric_values": [{"metric_id": metric_id, "value_baseline": 10, "value_current": 15}],
            "checkpoints": [],
        },
        headers=headers,
    )
    _assert_v1_error_envelope(
        load_response,
        status_code=409,
        expected_code="POSTGRES_RUNTIME_UNAVAILABLE",
        expected_message="Runtime Postgres indisponivel para carga inicial de indicadores.",
    )


def test_indicator_load_returns_json_fallback_forbidden_in_production_like(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://runtime-db")
    _override_indicator_service_with_repositories(
        measurements=_JsonBackendMeasurementRepository(),
        checkpoints=_JsonBackendCheckpointRepository(),
    )
    client = TestClient(app)
    try:
        admin_token = _login(client, "admin@swaif.local", "admin123")
        headers = {"Authorization": f"Bearer {admin_token}"}

        student_id, metric_id = _prepare_student_and_metric(client, headers)
        load_response = client.post(
            f"/admin/alunos/{student_id}/indicadores/carga-inicial",
            json={
                "metric_values": [{"metric_id": metric_id, "value_baseline": 10, "value_current": 15}],
                "checkpoints": [],
            },
            headers=headers,
        )
        _assert_v1_error_envelope(
            load_response,
            status_code=409,
            expected_code="JSON_FALLBACK_FORBIDDEN",
            expected_message="Fallback JSON proibido para carga inicial em runtime production-like.",
        )
    finally:
        app.dependency_overrides.pop(get_indicator_carga_service, None)


class _NoJsonMeasurementRepository:
    def replace_for_enrollment(self, enrollment_id: str, rows: list[dict]) -> list[dict]:
        return []

    def list_measurements(self) -> list[dict]:
        return []


class _NoJsonCheckpointRepository:
    def replace_for_enrollment(self, enrollment_id: str, rows: list[dict]) -> list[dict]:
        return []

    def list_by_enrollment(self, enrollment_id: str) -> list[dict]:
        return []


def test_indicator_load_returns_postgres_domain_not_ready_when_json_fallback_is_not_possible(monkeypatch, tmp_path: Path) -> None:
    _configure_stores(monkeypatch, tmp_path)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://runtime-db")

    def _non_json_service() -> IndicatorCargaService:
        return IndicatorCargaService(
            students=StudentRepository(),
            organizations=OrganizationRepository(),
            enrollments=EnrollmentRepository(),
            product_assignments=ProductAssignmentRepository(),
            metrics=MetricRepository(),
            measurements=_NoJsonMeasurementRepository(),
            checkpoints=_NoJsonCheckpointRepository(),
            pillars=PillarRepository(),
            measurement_overalls=MeasurementOverallRepository(),
        )

    app.dependency_overrides[get_indicator_carga_service] = _non_json_service
    try:
        client = TestClient(app)
        admin_token = _login(client, "admin@swaif.local", "admin123")
        headers = {"Authorization": f"Bearer {admin_token}"}
        student_id, metric_id = _prepare_student_and_metric(client, headers)

        load_response = client.post(
            f"/admin/alunos/{student_id}/indicadores/carga-inicial",
            json={
                "metric_values": [{"metric_id": metric_id, "value_baseline": 10, "value_current": 15}],
                "checkpoints": [],
            },
            headers=headers,
        )
        _assert_v1_error_envelope(
            load_response,
            status_code=409,
            expected_code="POSTGRES_DOMAIN_NOT_READY",
            expected_message="Dominios Postgres de indicadores ainda nao estao prontos para este fluxo.",
        )
    finally:
        app.dependency_overrides.pop(get_indicator_carga_service, None)
