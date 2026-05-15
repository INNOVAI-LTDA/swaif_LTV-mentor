from __future__ import annotations

from app.operations.sync_runtime_stores_from_supabase import SupabaseSyncConfig, _build_runtime_payloads


def test_build_runtime_payloads_maps_supabase_data_to_runtime_stores() -> None:
    source = {
        "users": [
            {
                "id": 1,
                "email": "mentor@example.com",
                "role": "provider",
                "full_name": "Mentor One",
                "is_active": True,
                "organization_id": None,
                "created_at": "2026-05-01T10:00:00Z",
                "updated_at": "2026-05-01T10:00:00Z",
                "password_hash": None,
            },
            {
                "id": 2,
                "email": "student@example.com",
                "role": "client",
                "full_name": "Student Two",
                "is_active": True,
                "organization_id": None,
                "created_at": "2026-05-01T10:00:00Z",
                "updated_at": "2026-05-01T10:00:00Z",
                "password_hash": None,
            },
        ],
        "organizations": [
            {
                "id": 99,
                "name": "Org Legacy",
                "brand_name": "Org Legacy",
                "slug": "org-legacy",
                "status": "active",
                "is_active": True,
                "created_at": "2026-05-01T10:00:00Z",
                "updated_at": "2026-05-01T10:00:00Z",
            }
        ],
        "products": [
            {
                "id": 10,
                "organization_id": 99,
                "name": "Mentoria Alpha",
                "slug": "mentoria-alpha",
                "status": "active",
                "created_at": "2026-05-01T10:00:00Z",
                "updated_at": "2026-05-01T10:00:00Z",
            }
        ],
        "pillars": [
            {
                "id": 20,
                "product_id": 10,
                "name": "Capacidade",
                "slug": "capacidade",
                "order_index": 1,
                "metadata": {},
                "is_active": True,
            }
        ],
        "metrics": [
            {
                "id": 30,
                "pillar_id": 20,
                "name": "Consultas",
                "slug": "consultas",
                "direction": "higher_better",
                "unit": None,
                "scoring_rules": {"version": 2},
                "score_type": "static",
                "min_score": 0,
                "max_score": 10,
                "max_score_basis": "MAX_VALUE",
                "mcv": 8,
                "is_active": True,
            }
        ],
        "enrollments": [
            {
                "id": 40,
                "provider_user_id": 1,
                "client_user_id": 2,
                "product_id": 10,
                "days_left": 30,
                "investment": 1500.5,
                "status": "active",
                "created_at": "2026-05-01T10:00:00Z",
                "updated_at": "2026-05-01T10:00:00Z",
            }
        ],
    }

    payloads = _build_runtime_payloads(
        source,
        SupabaseSyncConfig(
            database_url="postgres://fake",
            default_admin_password="admin123",
            default_provider_password="mentor123",
            default_client_password="aluno_accmed",
        ),
    )

    organizations = payloads["organizations"]["items"]
    protocols = payloads["protocols"]["items"]
    pillars = payloads["pillars"]["items"]
    metrics = payloads["metrics"]["items"]
    enrollments = payloads["enrollments"]["items"]
    measurements = payloads["measurements"]["items"]
    contacts = payloads["contacts_users_v2"]["items"]
    users = payloads["users"]["items"]

    assert len(organizations) == 1
    assert organizations[0]["id"] == "org_10"
    assert organizations[0]["name"] == "Mentoria Alpha"

    assert len(protocols) == 1
    assert protocols[0]["id"] == "prt_10"

    assert len(pillars) == 1
    assert pillars[0]["id"] == "plr_20"
    assert pillars[0]["protocol_id"] == "prt_10"

    assert len(metrics) == 1
    assert metrics[0]["id"] == "met_30"
    assert metrics[0]["pillar_id"] == "plr_20"

    assert len(enrollments) == 1
    assert enrollments[0]["id"] == "enr_40"
    assert enrollments[0]["mentor_id"] == "mtr_1"
    assert enrollments[0]["student_id"] == "std_2"
    assert enrollments[0]["organization_id"] == "org_10"
    assert enrollments[0]["ltv_cents"] == 150050

    assert len(measurements) == 1
    assert measurements[0]["enrollment_id"] == "enr_40"
    assert measurements[0]["metric_id"] == "met_30"
    assert measurements[0]["value_projected"] >= measurements[0]["value_current"]

    provider_contact = next(item for item in contacts if item["email"] == "mentor@example.com")
    assert provider_contact["role"] == "provider"
    assert str(provider_contact["password_hash"]).startswith("pbkdf2_sha256$")

    provider_user = next(item for item in users if item["email"] == "mentor@example.com")
    assert provider_user["role"] == "mentor"
