import json

from app.operations.export_canonical_data import export_canonical_data


def test_export_canonical_data_writes_target_store_set(tmp_path, monkeypatch) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    (data_dir / "clients.json").write_text(
        json.dumps(
            {
                "version": 1,
                "items": [
                    {
                        "id": "cli_1",
                        "name": "Cliente Um",
                        "brand_name": "Cliente Um",
                        "cnpj": "123",
                        "slug": "cliente-um",
                        "status": "active",
                        "is_active": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (data_dir / "organizations.json").write_text(
        json.dumps(
            {
                "version": 1,
                "items": [
                    {
                        "id": "org_1",
                        "client_id": "cli_1",
                        "name": "Produto Um",
                        "code": "PROD1",
                        "slug": "produto-um",
                        "mentor_id": "mtr_1",
                        "status": "active",
                        "is_active": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (data_dir / "mentors.json").write_text(
        json.dumps(
            {"version": 1, "items": [{"id": "mtr_1", "full_name": "Ana", "email": "ana@example.com", "organization_id": "org_1"}]}
        ),
        encoding="utf-8",
    )
    (data_dir / "students.json").write_text(
        json.dumps(
            {"version": 1, "items": [{"id": "std_1", "full_name": "Leo", "initials": "LE", "email": "leo@example.com"}]}
        ),
        encoding="utf-8",
    )
    (data_dir / "enrollments.json").write_text(
        json.dumps(
            {
                "version": 1,
                "items": [
                    {
                        "id": "enr_1",
                        "student_id": "std_1",
                        "organization_id": "org_1",
                        "mentor_id": "mtr_1",
                        "progress_score": 0.5,
                        "engagement_score": 0.7,
                        "urgency_status": "watch",
                        "day": 12,
                        "total_days": 90,
                        "days_left": 78,
                        "ltv_cents": 50000,
                        "is_active": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (data_dir / "protocols.json").write_text(
        json.dumps({"version": 1, "items": [{"id": "prt_1", "organization_id": "org_1", "name": "Metodo", "code": "metodo"}]}),
        encoding="utf-8",
    )
    (data_dir / "pillars.json").write_text(
        json.dumps({"version": 1, "items": [{"id": "plr_1", "protocol_id": "prt_1", "name": "Pilar", "code": "pilar", "order_index": 1}]}),
        encoding="utf-8",
    )
    (data_dir / "metrics.json").write_text(
        json.dumps(
            {
                "version": 1,
                "items": [{"id": "met_1", "protocol_id": "prt_1", "pillar_id": "plr_1", "name": "Indicador", "code": "indicador"}],
            }
        ),
        encoding="utf-8",
    )
    (data_dir / "measurements.json").write_text(
        json.dumps(
            {
                "version": 1,
                "items": [{"id": "mea_1", "enrollment_id": "enr_1", "metric_id": "met_1", "value_baseline": 10, "value_current": 12}],
            }
        ),
        encoding="utf-8",
    )
    (data_dir / "checkpoints.json").write_text(
        json.dumps({"version": 1, "items": [{"id": "chk_1", "enrollment_id": "enr_1", "week": 1, "status": "green", "label": "Inicio"}]}),
        encoding="utf-8",
    )

    monkeypatch.setenv("CLIENT_STORE_PATH", str(data_dir / "clients.json"))
    monkeypatch.setenv("ORG_STORE_PATH", str(data_dir / "organizations.json"))
    monkeypatch.setenv("MENTOR_STORE_PATH", str(data_dir / "mentors.json"))
    monkeypatch.setenv("STUDENT_STORE_PATH", str(data_dir / "students.json"))
    monkeypatch.setenv("ENROLLMENT_STORE_PATH", str(data_dir / "enrollments.json"))
    monkeypatch.setenv("PROTOCOL_STORE_PATH", str(data_dir / "protocols.json"))
    monkeypatch.setenv("PILLAR_STORE_PATH", str(data_dir / "pillars.json"))
    monkeypatch.setenv("METRIC_STORE_PATH", str(data_dir / "metrics.json"))
    monkeypatch.setenv("MEASUREMENT_STORE_PATH", str(data_dir / "measurements.json"))
    monkeypatch.setenv("CHECKPOINT_STORE_PATH", str(data_dir / "checkpoints.json"))

    written = export_canonical_data(tmp_path / "canonical")

    assert set(written.keys()) == {
        "clients.json",
        "products.json",
        "providers.json",
        "end_users.json",
        "product_pillars.json",
        "pillar_metrics.json",
        "product_assignments.json",
        "metric_measures.json",
        "journey_checkpoints.json",
    }

    assignments_payload = json.loads((tmp_path / "canonical" / "product_assignments.json").read_text(encoding="utf-8"))
    measures_payload = json.loads((tmp_path / "canonical" / "metric_measures.json").read_text(encoding="utf-8"))

    assert assignments_payload["items"][0]["product_id"] == "org_1"
    assert assignments_payload["items"][0]["provider_id"] == "mtr_1"
    assert assignments_payload["items"][0]["end_user_id"] == "std_1"
    assert assignments_payload["items"][0]["client_id"] == "cli_1"
    assert measures_payload["items"][0]["product_assignment_id"] == "enr_1"
    assert measures_payload["items"][0]["pillar_metric_id"] == "met_1"
