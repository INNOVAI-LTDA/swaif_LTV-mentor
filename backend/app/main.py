import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors import http_exception_handler, request_validation_exception_handler
from app.api.routes.admin_clients import router as admin_clients_router
from app.api.routes.admin_metrics import router as admin_metrics_router
from app.api.routes.admin_mentors import router as admin_mentors_router
from app.api.routes.admin_pillars import router as admin_pillars_router
from app.api.routes.admin_products import router as admin_products_router
from app.api.routes.admin_students import router as admin_students_router
from app.api.routes.admin_method_config import router as admin_method_config_router
from app.api.routes.admin_mentoria import router as admin_mentoria_router
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.mentor_demo import router as mentor_demo_router
from app.config.runtime import (
    get_app_env,
    get_client_code,
    get_storage_backup_dir,
    resolve_mentor_demo_route_policy,
    resolve_cors_origins,
)
from app.storage.checkpoint_repository import CheckpointRepository
from app.storage.catalog import resolve_storage_root
from app.storage.client_repository import ClientRepository
from app.storage.enrollment_repository import EnrollmentRepository
from app.storage.measurement_repository import MeasurementRepository
from app.storage.metric_repository import MetricRepository
from app.storage.mentor_repository import MentorRepository
from app.storage.organization_repository import OrganizationRepository
from app.storage.pillar_repository import PillarRepository
from app.storage.protocol_repository import ProtocolRepository
from app.storage.student_repository import StudentRepository
from app.storage.user_repository import UserRepository


logger = logging.getLogger("swaif.runtime")


def configure_runtime_logging() -> None:
    if logging.getLogger().handlers:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def create_app() -> FastAPI:
    configure_runtime_logging()
    app = FastAPI(title="SWAIF Mentoria API", version="0.1.0")
    app_env = get_app_env()
    client_code = get_client_code(app_env)
    cors_origins = resolve_cors_origins()
    allow_all_origins = "*" in cors_origins
    mentor_demo_policy = resolve_mentor_demo_route_policy(app_env)
    mentor_demo_enabled = mentor_demo_policy.enabled

    app.state.runtime_summary = {
        "app_env": app_env,
        "client_code": client_code,
        "cors_origins": cors_origins,
        "mentor_demo_routes_enabled": mentor_demo_enabled,
        "mentor_demo_policy_source": mentor_demo_policy.policy_source,
        "storage_root": str(resolve_storage_root()),
        "backup_dir": str(get_storage_backup_dir()),
    }

    logger.info(
        "backend_runtime_configured app_env=%s client_code=%s cors_origins=%s mentor_demo_routes=%s mentor_demo_policy=%s storage_root=%s backup_dir=%s",
        app.state.runtime_summary["app_env"],
        app.state.runtime_summary["client_code"],
        ",".join(app.state.runtime_summary["cors_origins"]),
        app.state.runtime_summary["mentor_demo_routes_enabled"],
        app.state.runtime_summary["mentor_demo_policy_source"],
        app.state.runtime_summary["storage_root"],
        app.state.runtime_summary["backup_dir"],
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if allow_all_origins else cors_origins,
        allow_credentials=not allow_all_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(admin_clients_router)
    app.include_router(admin_products_router)
    app.include_router(admin_mentors_router)
    app.include_router(admin_pillars_router)
    app.include_router(admin_metrics_router)
    app.include_router(admin_mentoria_router)
    app.include_router(admin_method_config_router)
    app.include_router(admin_students_router)
    if mentor_demo_enabled:
        app.include_router(mentor_demo_router)
    return app


app = create_app()


@app.on_event("startup")
def bootstrap_user_storage() -> None:
    UserRepository().list_users()
    ClientRepository().list_clients()
    OrganizationRepository().list_organizations()
    MentorRepository().list_mentors()
    ProtocolRepository().list_protocols()
    PillarRepository().list_pillars()
    MetricRepository().list_metrics()
    StudentRepository().list_students()
    EnrollmentRepository().list_enrollments()
    MeasurementRepository().list_measurements()
    CheckpointRepository().list_checkpoints()

    summary = app.state.runtime_summary
    logger.info(
        "backend_startup_complete app_env=%s client_code=%s cors_origins=%s mentor_demo_routes=%s mentor_demo_policy=%s storage_root=%s backup_dir=%s",
        summary["app_env"],
        summary["client_code"],
        ",".join(summary["cors_origins"]),
        summary["mentor_demo_routes_enabled"],
        summary["mentor_demo_policy_source"],
        summary["storage_root"],
        summary["backup_dir"],
    )
    if summary["mentor_demo_routes_enabled"]:
        logger.warning(
            "mentor_demo_routes_enabled=true; keep this restricted to local/demo validation environments."
        )
