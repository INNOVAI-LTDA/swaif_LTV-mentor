from __future__ import annotations

from collections.abc import Iterable

from app.schemas.canonical import (
    ClientRecord,
    EndUserRecord,
    JourneyCheckpointRecord,
    MetricMeasureRecord,
    PillarMetricRecord,
    ProductAssignmentRecord,
    ProductPillarRecord,
    ProductRecord,
    ProviderRecord,
)
from app.storage.checkpoint_repository import CheckpointRepository
from app.storage.client_repository import ClientRepository
from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.measurement_repository import MeasurementRepository
from app.storage.mentor_repository import MentorRepository
from app.storage.metric_repository import MetricRepository
from app.storage.organization_repository import OrganizationRepository
from app.storage.pillar_repository import PillarRepository
from app.storage.protocol_repository import ProtocolRepository
from app.storage.student_repository import StudentRepository


class CanonicalClientRepository:
    def __init__(self, clients: ClientRepository | None = None) -> None:
        self._clients = clients or ClientRepository()

    def list_records(self) -> list[ClientRecord]:
        return [ClientRecord.model_validate(item) for item in self._clients.list_clients()]


class CanonicalProductRepository:
    def __init__(self, products: OrganizationRepository | None = None) -> None:
        self._products = products or OrganizationRepository()

    def list_records(self) -> list[ProductRecord]:
        return [self._to_record(item) for item in self._products.list_organizations()]

    def list_by_client(self, client_id: str) -> list[ProductRecord]:
        return [self._to_record(item) for item in self._products.list_by_client(client_id)]

    def get_by_id(self, product_id: str) -> ProductRecord | None:
        item = self._products.get_by_id(product_id)
        return None if item is None else self._to_record(item)

    @staticmethod
    def _to_record(item: dict) -> ProductRecord:
        return ProductRecord(
            id=str(item["id"]),
            client_id=_optional_str(item.get("client_id")),
            name=str(item.get("name") or ""),
            code=_optional_str(item.get("code")),
            slug=_optional_str(item.get("slug")),
            status=_optional_str(item.get("status")),
            is_active=bool(item.get("is_active", True)),
            description=_optional_str(item.get("description")),
            delivery_model=_optional_str(item.get("delivery_model")),
            primary_provider_id=_optional_str(item.get("mentor_id")),
            created_at=_optional_str(item.get("created_at")),
            updated_at=_optional_str(item.get("updated_at")),
        )


class CanonicalProviderRepository:
    def __init__(
        self,
        providers: MentorRepository | None = None,
        products: OrganizationRepository | None = None,
    ) -> None:
        self._providers = providers or MentorRepository()
        self._products = CanonicalProductRepository(products)

    def list_records(self) -> list[ProviderRecord]:
        products_by_id = {item.id: item for item in self._products.list_records()}
        return [self._to_record(item, products_by_id=products_by_id) for item in self._providers.list_mentors()]

    def get_by_id(self, provider_id: str) -> ProviderRecord | None:
        products_by_id = {item.id: item for item in self._products.list_records()}
        item = self._providers.get_by_id(provider_id)
        return None if item is None else self._to_record(item, products_by_id=products_by_id)

    @staticmethod
    def _to_record(item: dict, *, products_by_id: dict[str, ProductRecord]) -> ProviderRecord:
        product_id = _optional_str(item.get("organization_id"))
        product = products_by_id.get(product_id or "")
        return ProviderRecord(
            id=str(item["id"]),
            client_id=product.client_id if product else None,
            product_id=product_id,
            full_name=str(item.get("full_name") or ""),
            email=str(item.get("email") or ""),
            cpf=_optional_str(item.get("cpf")),
            phone=_optional_str(item.get("phone")),
            bio=_optional_str(item.get("bio")),
            notes=_optional_str(item.get("notes")),
            status=_optional_str(item.get("status")),
            is_active=bool(item.get("is_active", True)),
            created_at=_optional_str(item.get("created_at")),
            updated_at=_optional_str(item.get("updated_at")),
        )


class CanonicalProductAssignmentRepository:
    def __init__(
        self,
        assignments: EnrollmentRepository | None = None,
        products: OrganizationRepository | None = None,
    ) -> None:
        self._assignments = assignments or EnrollmentRepository()
        self._products = CanonicalProductRepository(products)

    def list_records(self) -> list[ProductAssignmentRecord]:
        products_by_id = {item.id: item for item in self._products.list_records()}
        return [self._to_record(item, products_by_id=products_by_id) for item in self._assignments.list_enrollments()]

    def get_by_id(self, assignment_id: str) -> ProductAssignmentRecord | None:
        products_by_id = {item.id: item for item in self._products.list_records()}
        item = self._assignments.get_by_id(assignment_id)
        return None if item is None else self._to_record(item, products_by_id=products_by_id)

    @staticmethod
    def _to_record(item: dict, *, products_by_id: dict[str, ProductRecord]) -> ProductAssignmentRecord:
        product_id = str(item.get("organization_id") or "")
        product = products_by_id.get(product_id)
        return ProductAssignmentRecord(
            id=str(item["id"]),
            client_id=product.client_id if product else None,
            product_id=product_id,
            provider_id=_optional_str(item.get("mentor_id")),
            end_user_id=str(item.get("student_id") or ""),
            progress_score=float(item.get("progress_score") or 0),
            engagement_score=float(item.get("engagement_score") or 0),
            urgency_status=str(item.get("urgency_status") or "normal"),
            day=int(item.get("day") or 0),
            total_days=int(item.get("total_days") or 0),
            days_left=int(item.get("days_left") or 0),
            ltv_cents=int(item.get("ltv_cents") or 0),
            link_reason=_optional_str(item.get("link_reason")),
            source_assignment_id=_optional_str(item.get("source_enrollment_id")),
            created_by=_optional_str(item.get("created_by")),
            deactivated_at=_optional_str(item.get("deactivated_at")),
            deactivated_reason=_optional_str(item.get("deactivated_reason")),
            deactivated_by=_optional_str(item.get("deactivated_by")),
            reassigned_to_provider_id=_optional_str(item.get("reassigned_to_mentor_id")),
            is_active=bool(item.get("is_active", True)),
            created_at=_optional_str(item.get("created_at")),
            updated_at=_optional_str(item.get("updated_at")),
        )


class CanonicalEndUserRepository:
    def __init__(
        self,
        end_users: StudentRepository | None = None,
        assignments: EnrollmentRepository | None = None,
        products: OrganizationRepository | None = None,
    ) -> None:
        self._end_users = end_users or StudentRepository()
        self._assignments = CanonicalProductAssignmentRepository(assignments, products)

    def list_records(self) -> list[EndUserRecord]:
        client_by_end_user = self._build_client_lookup(self._assignments.list_records())
        return [self._to_record(item, client_by_end_user=client_by_end_user) for item in self._end_users.list_students()]

    @staticmethod
    def _build_client_lookup(assignments: Iterable[ProductAssignmentRecord]) -> dict[str, str]:
        client_by_end_user: dict[str, str] = {}
        for item in assignments:
            if item.client_id and item.end_user_id not in client_by_end_user:
                client_by_end_user[item.end_user_id] = item.client_id
        return client_by_end_user

    @staticmethod
    def _to_record(item: dict, *, client_by_end_user: dict[str, str]) -> EndUserRecord:
        end_user_id = str(item["id"])
        return EndUserRecord(
            id=end_user_id,
            client_id=client_by_end_user.get(end_user_id),
            full_name=str(item.get("full_name") or ""),
            initials=_optional_str(item.get("initials")),
            email=_optional_str(item.get("email")),
            cpf=_optional_str(item.get("cpf")),
            phone=_optional_str(item.get("phone")),
            notes=_optional_str(item.get("notes")),
            status=_optional_str(item.get("status")),
            is_active=bool(item.get("is_active", True)),
            created_at=_optional_str(item.get("created_at")),
            updated_at=_optional_str(item.get("updated_at")),
        )


class CanonicalProductPillarRepository:
    def __init__(
        self,
        protocols: ProtocolRepository | None = None,
        pillars: PillarRepository | None = None,
    ) -> None:
        self._protocols = protocols or ProtocolRepository()
        self._pillars = pillars or PillarRepository()

    def list_records(self) -> list[ProductPillarRecord]:
        protocols_by_id = {str(item.get("id")): item for item in self._protocols.list_protocols()}
        return [self._to_record(item, protocols_by_id=protocols_by_id) for item in self._pillars.list_pillars()]

    @staticmethod
    def _to_record(item: dict, *, protocols_by_id: dict[str, dict]) -> ProductPillarRecord:
        protocol = protocols_by_id.get(str(item.get("protocol_id") or ""), {})
        metadata = dict(item.get("metadata") or {})
        axis_sub = _optional_str(metadata.get("axis_sub"))
        if axis_sub is not None:
            metadata = {**metadata}
            metadata.pop("axis_sub", None)

        return ProductPillarRecord(
            id=str(item["id"]),
            product_id=str(protocol.get("organization_id") or ""),
            method_version_id=_optional_str(protocol.get("id")),
            method_version_name=_optional_str(protocol.get("name")),
            method_version_code=_optional_str(protocol.get("code")),
            name=str(item.get("name") or ""),
            code=_optional_str(item.get("code")),
            order_index=int(item.get("order_index") or 0),
            axis_sub=axis_sub,
            metadata=metadata,
            is_active=bool(item.get("is_active", True)),
        )


class CanonicalPillarMetricRepository:
    def __init__(
        self,
        protocols: ProtocolRepository | None = None,
        pillars: PillarRepository | None = None,
        metrics: MetricRepository | None = None,
    ) -> None:
        self._protocols = protocols or ProtocolRepository()
        self._pillars = pillars or PillarRepository()
        self._metrics = metrics or MetricRepository()

    def list_records(self) -> list[PillarMetricRecord]:
        protocols_by_id = {str(item.get("id")): item for item in self._protocols.list_protocols()}
        pillars_by_id = {str(item.get("id")): item for item in self._pillars.list_pillars()}
        return [
            self._to_record(item, protocols_by_id=protocols_by_id, pillars_by_id=pillars_by_id)
            for item in self._metrics.list_metrics()
        ]

    @staticmethod
    def _to_record(
        item: dict,
        *,
        protocols_by_id: dict[str, dict],
        pillars_by_id: dict[str, dict],
    ) -> PillarMetricRecord:
        protocol = protocols_by_id.get(str(item.get("protocol_id") or ""), {})
        pillar = pillars_by_id.get(str(item.get("pillar_id") or ""), {})
        return PillarMetricRecord(
            id=str(item["id"]),
            product_id=str(protocol.get("organization_id") or ""),
            product_pillar_id=str(pillar.get("id") or item.get("pillar_id") or ""),
            method_version_id=_optional_str(protocol.get("id")),
            name=str(item.get("name") or ""),
            code=_optional_str(item.get("code")),
            direction=_optional_str(item.get("direction")),
            unit=_optional_str(item.get("unit")),
            metadata=dict(item.get("metadata") or {}),
            is_active=bool(item.get("is_active", True)),
        )


class CanonicalMetricMeasureRepository:
    def __init__(self, measurements: MeasurementRepository | None = None) -> None:
        self._measurements = measurements or MeasurementRepository()

    def list_records(self) -> list[MetricMeasureRecord]:
        return [
            MetricMeasureRecord(
                id=str(item["id"]),
                product_assignment_id=str(item.get("enrollment_id") or ""),
                pillar_metric_id=str(item.get("metric_id") or ""),
                value_baseline=None if item.get("value_baseline") is None else float(item.get("value_baseline")),
                value_current=float(item.get("value_current") or 0),
                value_projected=None if item.get("value_projected") is None else float(item.get("value_projected")),
                improving_trend=item.get("improving_trend"),
            )
            for item in self._measurements.list_measurements()
        ]


class CanonicalJourneyCheckpointRepository:
    def __init__(self, checkpoints: CheckpointRepository | None = None) -> None:
        self._checkpoints = checkpoints or CheckpointRepository()

    def list_records(self) -> list[JourneyCheckpointRecord]:
        return [
            JourneyCheckpointRecord(
                id=str(item["id"]),
                product_assignment_id=str(item.get("enrollment_id") or ""),
                week=int(item.get("week") or 0),
                status=str(item.get("status") or ""),
                label=_optional_str(item.get("label")),
            )
            for item in self._checkpoints.list_checkpoints()
        ]


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
