from __future__ import annotations

from typing import Any

from app.storage.mentor_repository import MentorRepository
from app.storage.organization_repository import OrganizationRepository


class EntityNotFoundError(Exception):
    pass


class ValidationError(Exception):
    pass


class AdminMentorService:
    def __init__(self, organizations: OrganizationRepository, mentors: MentorRepository) -> None:
        self._organizations = organizations
        self._mentors = mentors

    def _get_active_product(self, product_id: str) -> dict[str, Any]:
        product = self._organizations.get_by_id(product_id)
        if not product or not bool(product.get("is_active", True)):
            raise EntityNotFoundError("product not found")
        return product

    def list_mentors_by_product(self, product_id: str) -> list[dict[str, Any]]:
        product = self._get_active_product(product_id)
        items = [
            item
            for item in self._mentors.list_by_organization(product["id"])
            if bool(item.get("is_active", True))
        ]
        return sorted(items, key=lambda item: (str(item.get("full_name") or "").lower(), str(item.get("email") or "").lower()))

    def create_mentor(
        self,
        *,
        product_id: str,
        full_name: str,
        cpf: str,
        email: str,
        phone: str | None = None,
        bio: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        product = self._get_active_product(product_id)

        normalized_name = full_name.strip()
        normalized_email = email.strip().lower()
        normalized_cpf = "".join(char for char in cpf if char.isdigit())
        if not normalized_name or not normalized_email or not normalized_cpf:
            raise ValidationError("full_name, cpf and email are required")

        mentor = self._mentors.create(
            full_name=normalized_name,
            cpf=normalized_cpf,
            email=normalized_email,
            organization_id=product["id"],
            phone=phone,
            bio=bio,
            notes=notes,
        )
        self._organizations.set_mentor(product["id"], mentor["id"])
        return mentor
