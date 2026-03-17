from app.services.mentoria_service import EntityNotFoundError, MentoriaService


class _FakeOrganizationRepository:
    def __init__(self) -> None:
        self.items: dict[str, dict] = {}
        self._seq = 0

    def create(self, *, name: str, slug: str | None = None) -> dict:
        self._seq += 1
        organization = {
            "id": f"org_{self._seq}",
            "name": name,
            "slug": slug or f"org-{self._seq}",
            "mentor_id": None,
            "is_active": True,
        }
        self.items[organization["id"]] = organization
        return organization

    def get_by_id(self, organization_id: str) -> dict | None:
        return self.items.get(organization_id)

    def set_mentor(self, organization_id: str, mentor_id: str) -> dict:
        self.items[organization_id]["mentor_id"] = mentor_id
        return self.items[organization_id]


class _FakeMentorRepository:
    def __init__(self) -> None:
        self.items: dict[str, dict] = {}
        self._seq = 0

    def create(self, *, full_name: str, email: str) -> dict:
        self._seq += 1
        mentor = {
            "id": f"mtr_{self._seq}",
            "full_name": full_name,
            "email": email,
            "is_active": True,
        }
        self.items[mentor["id"]] = mentor
        return mentor

    def get_by_id(self, mentor_id: str) -> dict | None:
        return self.items.get(mentor_id)

    def set_organization(self, mentor_id: str, organization_id: str) -> dict | None:
        mentor = self.items.get(mentor_id)
        if not mentor:
            return None
        mentor["organization_id"] = organization_id
        return mentor


def test_service_links_mentor_to_mentoria() -> None:
    org_repo = _FakeOrganizationRepository()
    mentor_repo = _FakeMentorRepository()
    service = MentoriaService(org_repo, mentor_repo)

    org = service.create_organization("Mentoria Alpha", "mentoria-alpha")
    mentor = service.create_mentor("Ana Mentora", "ana@swaif.local")
    linked = service.link_mentor_to_organization(org["id"], mentor["id"])

    assert linked["mentor_id"] == mentor["id"]


def test_service_raises_not_found_for_missing_entities() -> None:
    service = MentoriaService(_FakeOrganizationRepository(), _FakeMentorRepository())

    try:
        service.link_mentor_to_organization("org_missing", "mtr_missing")
        assert False, "expected EntityNotFoundError"
    except EntityNotFoundError:
        assert True
