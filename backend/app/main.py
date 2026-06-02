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
from app.api.routes.admin_provider_view import router as admin_provider_view_router
from app.api.routes.admin_database_view import router as admin_database_view_router
from app.api.routes.admin_api_operations import router as admin_api_operations_router
from app.api.routes.admin_students import router as admin_students_router
from app.api.routes.admin_method_config import router as admin_method_config_router
from app.api.routes.admin_mentoria import router as admin_mentoria_router
from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.mentor import router as mentor_router
from app.api.routes.provider import router as provider_router
from app.api.routes.student_workspace import router as student_workspace_router
from app.config.runtime import (
    get_app_env,
    get_client_code,
    get_cors_allow_origin_regex,
    get_supabase_db_url,
    get_supabase_sync_default_admin_password,
    get_supabase_sync_default_client_password,
    get_supabase_sync_default_provider_password,
    get_storage_backup_dir,
    resolve_mentor_route_policy,
    resolve_cors_origins,
    supabase_sync_on_startup_enabled,
)
from app.operations.sync_runtime_stores_from_supabase import (
    SupabaseSyncConfig,
    sync_runtime_stores_from_supabase,
)
from app.storage.catalog import resolve_storage_root
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
    cors_origin_regex = get_cors_allow_origin_regex()
    allow_all_origins = "*" in cors_origins
    mentor_route_policy = resolve_mentor_route_policy(app_env)
    mentor_routes_enabled = mentor_route_policy.enabled

    app.state.runtime_summary = {
        "app_env": app_env,
        "client_code": client_code,
        "cors_origins": cors_origins,
        "cors_origin_regex": cors_origin_regex,
        "mentor_routes_enabled": mentor_routes_enabled,
        "mentor_route_policy_source": mentor_route_policy.policy_source,
        # Legacy aliases kept for compatibility with older diagnostics consumers.
        "mentor_demo_routes_enabled": mentor_routes_enabled,
        "mentor_demo_policy_source": mentor_route_policy.policy_source,
        "supabase_sync_on_startup": supabase_sync_on_startup_enabled(),
        "storage_root": str(resolve_storage_root()),
        "backup_dir": str(get_storage_backup_dir()),
    }

    logger.info(
        "backend_runtime_configured app_env=%s client_code=%s cors_origins=%s cors_origin_regex=%s mentor_routes=%s mentor_route_policy=%s storage_root=%s backup_dir=%s",
        app.state.runtime_summary["app_env"],
        app.state.runtime_summary["client_code"],
        ",".join(app.state.runtime_summary["cors_origins"]),
        app.state.runtime_summary["cors_origin_regex"] or "none",
        app.state.runtime_summary["mentor_routes_enabled"],
        app.state.runtime_summary["mentor_route_policy_source"],
        app.state.runtime_summary["storage_root"],
        app.state.runtime_summary["backup_dir"],
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if allow_all_origins else cors_origins,
        allow_credentials=not allow_all_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_origin_regex=cors_origin_regex,
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
    app.include_router(admin_provider_view_router)
    app.include_router(admin_database_view_router)
    app.include_router(admin_api_operations_router)
    from app.api.routes.admin_users import router as admin_users_router
    app.include_router(admin_users_router)
    # Register admin_organizations router
    try:
        from app.api.routes.admin_organizations import router as admin_organizations_router
        app.include_router(admin_organizations_router)
    except ImportError:
        try:
            from backend.app.api.routes.admin_organizations import router as admin_organizations_router
            app.include_router(admin_organizations_router)
        except ImportError:
            import warnings
            warnings.warn("admin_organizations router could not be imported; /admin/organizations endpoint will be unavailable.")
    if mentor_routes_enabled:
        app.include_router(mentor_router)
    app.include_router(provider_router)
    app.include_router(student_workspace_router)
    return app


app = create_app()


@app.on_event("startup")
def bootstrap_user_storage() -> None:
    summary = app.state.runtime_summary
    if summary["supabase_sync_on_startup"]:
        logger.info("supabase_startup_sync_begin")
        database_url = get_supabase_db_url()
        if not database_url:
            raise RuntimeError("SUPABASE_SYNC_ON_STARTUP is enabled but SUPABASE_DB_URL is missing.")

        sync_result = sync_runtime_stores_from_supabase(
            SupabaseSyncConfig(
                database_url=database_url,
                default_admin_password=get_supabase_sync_default_admin_password(),
                default_provider_password=get_supabase_sync_default_provider_password(),
                default_client_password=get_supabase_sync_default_client_password(),
            )
        )
        summary["supabase_sync_written"] = sync_result.counters
        logger.info("supabase_startup_sync_completed counters=%s", sync_result.counters)

    # Keep startup resilient while legacy repositories are still being migrated
    # away from JSON storage: warm only auth-critical stores.
    logger.info("startup_warmup_begin target=user_repository")
    UserRepository().list_users()
    logger.info("startup_warmup_completed target=user_repository")
    logger.info("startup_warmup_begin target=student_repository")
    StudentRepository().list_students()
    logger.info("startup_warmup_completed target=student_repository")

    logger.info(
        "backend_startup_complete app_env=%s client_code=%s cors_origins=%s cors_origin_regex=%s mentor_routes=%s mentor_route_policy=%s supabase_sync_on_startup=%s storage_root=%s backup_dir=%s",
        summary["app_env"],
        summary["client_code"],
        ",".join(summary["cors_origins"]),
        summary["cors_origin_regex"] or "none",
        summary["mentor_routes_enabled"],
        summary["mentor_route_policy_source"],
        summary["supabase_sync_on_startup"],
        summary["storage_root"],
        summary["backup_dir"],
    )
    if summary["mentor_routes_enabled"]:
        logger.warning(
            "mentor_routes_enabled=true; keep this restricted to local-only validation environments."
        )
