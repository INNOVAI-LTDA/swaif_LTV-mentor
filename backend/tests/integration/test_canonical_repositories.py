from app.storage.canonical_repositories import (
    CanonicalEndUserRepository,
    CanonicalPillarMetricRepository,
    CanonicalProductAssignmentRepository,
    CanonicalProductPillarRepository,
    CanonicalProductRepository,
    CanonicalProviderRepository,
)
from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.mentor_repository import MentorRepository
from app.storage.metric_repository import MetricRepository
from app.storage.organization_repository import OrganizationRepository
from app.storage.pillar_repository import PillarRepository
from app.storage.protocol_repository import ProtocolRepository
from app.storage.student_repository import StudentRepository


def test_canonical_repositories_map_legacy_product_provider_end_user_and_assignment(tmp_path) -> None:
    org_repo = OrganizationRepository(tmp_path / "organizations.json")
    mentor_repo = MentorRepository(tmp_path / "mentors.json")
    student_repo = StudentRepository(tmp_path / "students.json")
    enrollment_repo = EnrollmentRepository(tmp_path / "enrollments.json")

    product = org_repo.create(name="Produto Growth", client_id="cli_1", code="GROWTH")
    provider = mentor_repo.create(
        full_name="Marina Provider",
        email="marina@example.com",
        organization_id=product["id"],
    )
    end_user = student_repo.create(full_name="Carlos End User", email="carlos@example.com")
    assignment = enrollment_repo.create(
        student_id=end_user["id"],
        organization_id=product["id"],
        mentor_id=provider["id"],
        progress_score=0.4,
        engagement_score=0.8,
        days_left=42,
        total_days=90,
        day=48,
        ltv_cents=150000,
    )

    products = CanonicalProductRepository(org_repo).list_records()
    providers = CanonicalProviderRepository(mentor_repo, org_repo).list_records()
    end_users = CanonicalEndUserRepository(student_repo, enrollment_repo, org_repo).list_records()
    assignments = CanonicalProductAssignmentRepository(enrollment_repo, org_repo).list_records()

    assert products[0].id == product["id"]
    assert products[0].client_id == "cli_1"
    assert products[0].primary_provider_id is None

    assert providers[0].id == provider["id"]
    assert providers[0].product_id == product["id"]
    assert providers[0].client_id == "cli_1"

    assert end_users[0].id == end_user["id"]
    assert end_users[0].client_id == "cli_1"

    assert assignments[0].id == assignment["id"]
    assert assignments[0].product_id == product["id"]
    assert assignments[0].provider_id == provider["id"]
    assert assignments[0].end_user_id == end_user["id"]
    assert assignments[0].client_id == "cli_1"
    assert assignments[0].days_left == 42


def test_canonical_repositories_map_protocol_structure_into_product_pillars_and_metrics(tmp_path) -> None:
    org_repo = OrganizationRepository(tmp_path / "organizations.json")
    protocol_repo = ProtocolRepository(tmp_path / "protocols.json")
    pillar_repo = PillarRepository(tmp_path / "pillars.json")
    metric_repo = MetricRepository(tmp_path / "metrics.json")

    product = org_repo.create(name="Produto Core", client_id="cli_7", code="CORE")
    protocol = protocol_repo.create(
        organization_id=product["id"],
        name="Metodo Principal",
        code="metodo-principal",
        metadata={"version": "v1"},
    )
    pillar = pillar_repo.create(
        protocol_id=protocol["id"],
        name="Pilar Valor",
        code="valor",
        order_index=2,
        metadata={"axis_sub": "Percepcao de valor"},
    )
    metric = metric_repo.create(
        protocol_id=protocol["id"],
        pillar_id=pillar["id"],
        name="NPS",
        code="nps",
        direction="higher_better",
        unit="%",
        scoring_rules=[{"type": "static", "score": 1}],
        score_type="static",
        min_score=0,
        max_score=1,
        mcv_score=1,
        max_basis_score=1,
    )

    product_pillars = CanonicalProductPillarRepository(protocol_repo, pillar_repo).list_records()
    pillar_metrics = CanonicalPillarMetricRepository(protocol_repo, pillar_repo, metric_repo).list_records()

    assert product_pillars[0].product_id == product["id"]
    assert product_pillars[0].method_version_id == protocol["id"]
    assert product_pillars[0].method_version_code == protocol["code"]
    assert product_pillars[0].axis_sub == "Percepcao de valor"

    assert pillar_metrics[0].product_id == product["id"]
    assert pillar_metrics[0].product_pillar_id == pillar["id"]
    assert pillar_metrics[0].method_version_id == protocol["id"]
    assert pillar_metrics[0].direction == "higher_better"
