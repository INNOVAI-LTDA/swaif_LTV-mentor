from __future__ import annotations

from typing import Any

from app.storage.mentor_repository import MentorRepository
from app.storage.organization_repository import OrganizationRepository


class EntityNotFoundError(Exception):
    pass


class MentoriaService:
    def __init__(self, organizations: OrganizationRepository, mentors: MentorRepository) -> None:
        self._organizations = organizations
        self._mentors = mentors

    def create_organization(self, name: str, slug: str | None = None) -> dict[str, Any]:
        return self._organizations.create(name=name, slug=slug)

    def create_mentor(self, full_name: str, email: str) -> dict[str, Any]:
        return self._mentors.create(full_name=full_name, email=email)

    def link_mentor_to_organization(self, organization_id: str, mentor_id: str) -> dict[str, Any]:
        organization = self._organizations.get_by_id(organization_id)
        if not organization:
            raise EntityNotFoundError("organization not found")

        mentor = self._mentors.get_by_id(mentor_id)
        if not mentor:
            raise EntityNotFoundError("mentor not found")

        updated_org = self._organizations.set_mentor(organization_id, mentor_id)
        self._mentors.set_organization(mentor_id, organization_id)
        if not updated_org:
            raise EntityNotFoundError("organization not found")
        return updated_org

    def get_organization_with_mentor(self, organization_id: str) -> dict[str, Any]:
        organization = self._organizations.get_by_id(organization_id)
        if not organization:
            raise EntityNotFoundError("organization not found")

        mentor = None
        mentor_id = organization.get("mentor_id")
        if mentor_id:
            mentor = self._mentors.get_by_id(str(mentor_id))

        return {**organization, "mentor": mentor}
