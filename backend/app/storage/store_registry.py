from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StorePathConfig:
    name: str
    env_var: str
    filename: str


STORE_PATH_CONFIGS = [
    StorePathConfig(name="users", env_var="USER_STORE_PATH", filename="users.json"),
    StorePathConfig(name="clients", env_var="CLIENT_STORE_PATH", filename="clients.json"),
    StorePathConfig(name="organizations", env_var="ORG_STORE_PATH", filename="organizations.json"),
    StorePathConfig(name="mentors", env_var="MENTOR_STORE_PATH", filename="mentors.json"),
    StorePathConfig(name="protocols", env_var="PROTOCOL_STORE_PATH", filename="protocols.json"),
    StorePathConfig(name="pillars", env_var="PILLAR_STORE_PATH", filename="pillars.json"),
    StorePathConfig(name="metrics", env_var="METRIC_STORE_PATH", filename="metrics.json"),
    StorePathConfig(name="students", env_var="STUDENT_STORE_PATH", filename="students.json"),
    StorePathConfig(name="enrollments", env_var="ENROLLMENT_STORE_PATH", filename="enrollments.json"),
    StorePathConfig(name="measurements", env_var="MEASUREMENT_STORE_PATH", filename="measurements.json"),
    StorePathConfig(name="checkpoints", env_var="CHECKPOINT_STORE_PATH", filename="checkpoints.json"),
]


def default_storage_data_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "data"


def resolve_store_path(env_var: str, filename: str) -> Path:
    configured = os.getenv(env_var)
    if configured:
        return Path(configured)
    return default_storage_data_dir() / filename


def resolve_registered_store_paths() -> list[tuple[str, Path]]:
    return [(config.name, resolve_store_path(config.env_var, config.filename)) for config in STORE_PATH_CONFIGS]
