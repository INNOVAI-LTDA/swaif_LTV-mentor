from app.storage.mentor_repository import MentorRepository
from app.storage.organization_repository import OrganizationRepository


def test_mentor_repository_creates_and_lists_by_product(tmp_path) -> None:
    org_repo = OrganizationRepository(tmp_path / "organizations.json")
    mentor_repo = MentorRepository(tmp_path / "mentors.json")

    product = org_repo.create(name="Acelerador Medico Premium", client_id="cli_1", code="AMP-PREMIUM")
    created = mentor_repo.create(
        full_name="Ana Mentora",
        cpf="123.456.789-00",
        email="ana@swaif.local",
        organization_id=product["id"],
    )

    assert created["id"] == "mtr_1"
    assert created["cpf"] == "12345678900"
    assert len(mentor_repo.list_by_organization(product["id"])) == 1


def test_mentor_repository_rejects_duplicate_cpf(tmp_path) -> None:
    mentor_repo = MentorRepository(tmp_path / "mentors.json")
    mentor_repo.create(full_name="Ana Mentora", cpf="12345678900", email="ana@swaif.local")

    try:
        mentor_repo.create(full_name="Bea Mentora", cpf="123.456.789-00", email="bea@swaif.local")
    except ValueError as exc:
        assert str(exc) == "mentor cpf already exists"
    else:
        raise AssertionError("ValueError was expected")
