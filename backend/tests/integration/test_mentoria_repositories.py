from pathlib import Path

from app.storage.mentor_repository import MentorRepository
from app.storage.organization_repository import OrganizationRepository


def test_organization_and_mentor_persist_and_link(tmp_path: Path) -> None:
    org_repo = OrganizationRepository(tmp_path / "organizations.json")
    mentor_repo = MentorRepository(tmp_path / "mentors.json")

    organization = org_repo.create(name="Mentoria Beta", slug="mentoria-beta")
    mentor = mentor_repo.create(full_name="Bruno Mentor", email="bruno@swaif.local")

    org_repo.set_mentor(organization_id=organization["id"], mentor_id=mentor["id"])
    reloaded = org_repo.get_by_id(organization["id"])

    assert reloaded is not None
    assert reloaded["mentor_id"] == mentor["id"]
