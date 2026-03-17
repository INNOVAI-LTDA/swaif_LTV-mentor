import os

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
from app.storage.checkpoint_repository import CheckpointRepository
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


app = FastAPI(title="SWAIF Mentoria API", version="0.1.0")
_cors_env = os.getenv("CORS_ALLOW_ORIGINS", "")
_cors_origins = [origin.strip() for origin in _cors_env.split(",") if origin.strip()]
if not _cors_origins:
    _cors_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
_allow_all_origins = "*" in _cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _allow_all_origins else _cors_origins,
    allow_credentials=not _allow_all_origins,
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
app.include_router(mentor_demo_router)


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
