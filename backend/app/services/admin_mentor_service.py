from __future__ import annotations

from typing import Any

from app.storage.contact_user_repository import ContactUserRepository
from app.storage.mentor_repository import MentorRepository
from app.storage.organization_repository import OrganizationRepository


class EntityNotFoundError(Exception):
    pass


class ValidationError(Exception):
    pass


class AdminMentorService:
    def __init__(self, organizations: OrganizationRepository, mentors: MentorRepository, contacts: ContactUserRepository) -> None:
        self._organizations = organizations
        self._mentors = mentors
        self._contacts = contacts

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
        if not items and str(product.get("mentor_id") or ""):
            contacts = [item for item in self._contacts.list_items() if str(item.get("role") or "") == "mentor" and bool(item.get("is_active", True)) and str(item.get("organization_id") or "") == product["id"]]
            items = contacts
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
        try:
            self._contacts.create(
                id=str(mentor["id"]),
                full_name=str(mentor.get("full_name") or normalized_name),
                email=normalized_email,
                role="mentor",
                is_active=True,
                cpf=normalized_cpf,
                phone=phone,
                organization_id=product["id"],
                notes=notes,
            )
        except ValueError:
            pass
        return mentor
