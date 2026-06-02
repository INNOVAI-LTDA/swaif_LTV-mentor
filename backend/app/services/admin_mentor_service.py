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
    def __init__(self, organizations: OrganizationRepository, mentors: MentorRepository | None, contacts: ContactUserRepository) -> None:
        self._organizations = organizations
        self._mentors = mentors
        self._contacts = contacts

    @staticmethod
    def _normalize_prefixed_id(value: Any, prefix: str) -> str:
        raw = str(value or "").strip()
        expected = f"{prefix}_"
        if raw.startswith(expected):
            return raw[len(expected):]
        return raw

    @staticmethod
    def _normalize_mentor_payload(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(item.get("id") or ""),
            "full_name": str(item.get("full_name") or item.get("name") or "").strip(),
            "email": str(item.get("email") or "").strip().lower(),
            "cpf": str(item.get("cpf") or "") or None,
            "phone": str(item.get("phone") or "") or None,
            "bio": str(item.get("bio") or "") or None,
            "notes": str(item.get("notes") or "") or None,
            "status": str(item.get("status") or "active"),
            "is_active": bool(item.get("is_active", True)),
            "organization_id": str(item.get("organization_id") or "") or None,
            "created_at": str(item.get("created_at") or "") or None,
            "updated_at": str(item.get("updated_at") or "") or None,
        }

    def _get_active_product(self, product_id: str) -> dict[str, Any]:
        product = self._organizations.get_by_id(product_id)
        if not product or not bool(product.get("is_active", True)):
            raise EntityNotFoundError("product not found")
        return product

    def list_mentors_by_product(self, product_id: str) -> list[dict[str, Any]]:
        product = self._get_active_product(product_id)
        items: list[dict[str, Any]] = []
        if self._mentors is not None:
            try:
                items = [
                    item
                    for item in self._mentors.list_by_organization(str(product["id"]))
                    if bool(item.get("is_active", True))
                ]
            except RuntimeError:
                # Runtime Supabase mode has JSON mentor repository disabled.
                items = []

        if not items:
            product_org = self._normalize_prefixed_id(product.get("id"), "org")
            contacts = []
            for item in self._contacts.list_items():
                role = str(item.get("role") or "").strip().lower()
                if role not in {"mentor", "provider"}:
                    continue
                if not bool(item.get("is_active", True)):
                    continue
                contact_org = self._normalize_prefixed_id(item.get("organization_id"), "org")
                if product_org and contact_org != product_org:
                    continue
                contacts.append(item)
            items = contacts

        normalized_items = [self._normalize_mentor_payload(item) for item in items]
        return sorted(normalized_items, key=lambda item: (str(item.get("full_name") or "").lower(), str(item.get("email") or "").lower()))

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
        if self._mentors is None:
            raise RuntimeError("mentor_write_not_supported_in_supabase_runtime")

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
