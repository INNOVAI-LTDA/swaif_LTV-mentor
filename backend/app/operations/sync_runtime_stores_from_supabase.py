from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.config.runtime import get_supabase_db_connect_timeout_seconds
from app.core.security import hash_password
from app.storage.postgres_indicator_repositories import (
    PostgresCheckpointRepository,
    PostgresMeasurementRepository,
)
from app.storage.store_registry import resolve_store_path

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None

logger = logging.getLogger("swaif.runtime")


@dataclass(frozen=True)
class SupabaseSyncConfig:
    database_url: str
    default_admin_password: str = "admin123"
    default_provider_password: str = "mentor123"
    default_client_password: str = "aluno_accmed"


@dataclass(frozen=True)
class SupabaseSyncResult:
    stores: dict[str, Path]
    counters: dict[str, int]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _iso(value: Any) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    raw = str(value or "").strip()
    return raw or _now_iso()


def _slugify(value: Any, *, fallback: str) -> str:
    normalized = "-".join(part for part in str(value or "").strip().lower().replace("_", "-").split() if part)
    return normalized or fallback


def _initials(full_name: str) -> str:
    parts = [part for part in full_name.split() if part]
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[1][0]}".upper()
    compact = "".join(parts)
    return (compact[:2] or "AL").upper()


def _deterministic_delta(*, enrollment_id: str, metric_id: str) -> float:
    digest = hashlib.sha256(f"{enrollment_id}:{metric_id}".encode("utf-8")).hexdigest()
    bucket = int(digest[:4], 16)
    return ((bucket % 21) - 10) / 100.0


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _query_rows(cursor: Any, query: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
    cursor.execute(query, params or ())
    columns = [column[0] for column in (cursor.description or [])]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _column_exists(cursor: Any, *, table_name: str, column_name: str) -> bool:
    cursor.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s AND column_name = %s
        LIMIT 1
        """,
        (table_name, column_name),
    )
    return cursor.fetchone() is not None


def _connect(database_url: str) -> Any:
    if psycopg is None:
        raise RuntimeError("psycopg is not installed. Install dependency before syncing runtime stores.")
    # Supabase shared pooler (transaction mode) is not compatible with prepared statements.
    return psycopg.connect(
        database_url,
        prepare_threshold=None,
        connect_timeout=get_supabase_db_connect_timeout_seconds(),
    )


def _fetch_source_rows(database_url: str) -> dict[str, list[dict[str, Any]]]:
    started = time.perf_counter()
    logger.info("supabase_sync_fetch_begin")
    with _connect(database_url) as conn:
        with conn.cursor() as cur:
            has_password_hash = _column_exists(cur, table_name="deva_accmed_users", column_name="password_hash")
            users_query = (
                """
                SELECT id, email, role, full_name, is_active, organization_id, created_at, updated_at, password_hash
                FROM deva_accmed_users
                """
                if has_password_hash
                else """
                SELECT id, email, role, full_name, is_active, organization_id, created_at, updated_at, NULL::text AS password_hash
                FROM deva_accmed_users
                """
            )

            result = {
                "users": _query_rows(cur, users_query),
                "organizations": _query_rows(
                    cur,
                    """
                    SELECT id, name, brand_name, slug, status, is_active, created_at, updated_at
                    FROM deva_accmed_organizations
                    """,
                ),
                "products": _query_rows(
                    cur,
                    """
                    SELECT id, organization_id, name, slug, status, created_at, updated_at
                    FROM deva_accmed_products
                    """,
                ),
                "pillars": _query_rows(
                    cur,
                    """
                    SELECT id, product_id, name, slug, order_index, metadata, is_active
                    FROM deva_accmed_product_pillars
                    """,
                ),
                "metrics": _query_rows(
                    cur,
                    """
                    SELECT id, pillar_id, name, slug, direction, unit, scoring_rules, score_type, min_score, max_score, max_score_basis, mcv, is_active
                    FROM deva_accmed_product_metrics
                    """,
                ),
                "enrollments": _query_rows(
                    cur,
                    """
                    SELECT id, provider_user_id, client_user_id, product_id, days_left, investment, status, created_at, updated_at
                    FROM deva_accmed_enrollments
                    """,
                ),
            }
            logger.info(
                "supabase_sync_fetch_completed users=%s organizations=%s products=%s pillars=%s metrics=%s enrollments=%s elapsed_ms=%s",
                len(result["users"]),
                len(result["organizations"]),
                len(result["products"]),
                len(result["pillars"]),
                len(result["metrics"]),
                len(result["enrollments"]),
                int((time.perf_counter() - started) * 1000),
            )
            return result


def _build_runtime_payloads(source: dict[str, list[dict[str, Any]]], config: SupabaseSyncConfig) -> dict[str, dict[str, Any]]:
    now_iso = _now_iso()
    products = source.get("products", [])
    pillars = source.get("pillars", [])
    metrics = source.get("metrics", [])
    enrollments = source.get("enrollments", [])
    users = source.get("users", [])

    product_by_id = {str(row.get("id")): row for row in products}
    pillar_by_id = {str(row.get("id")): row for row in pillars}

    providers_by_product: dict[str, str] = {}
    for row in enrollments:
        product_id = str(row.get("product_id") or "")
        provider_id = str(row.get("provider_user_id") or "")
        if product_id and provider_id and product_id not in providers_by_product:
            providers_by_product[product_id] = provider_id

    runtime_organizations: list[dict[str, Any]] = []
    runtime_protocols: list[dict[str, Any]] = []

    for product in products:
        product_id = str(product.get("id") or "")
        if not product_id:
            continue
        org_id = f"org_{product_id}"
        organization_id = str(product.get("organization_id") or "")
        runtime_organizations.append(
            {
                "id": org_id,
                "name": str(product.get("name") or f"Produto {product_id}"),
                "slug": _slugify(product.get("slug"), fallback=f"produto-{product_id}"),
                "code": _slugify(product.get("slug"), fallback=f"produto-{product_id}").upper().replace("-", "_"),
                "client_id": f"cli_{organization_id}" if organization_id else None,
                "mentor_id": f"mtr_{providers_by_product[product_id]}" if product_id in providers_by_product else None,
                "description": None,
                "delivery_model": "live",
                "status": str(product.get("status") or "active"),
                "is_active": str(product.get("status") or "active").lower() == "active",
                "created_at": _iso(product.get("created_at")),
                "updated_at": _iso(product.get("updated_at")),
            }
        )
        runtime_protocols.append(
            {
                "id": f"prt_{product_id}",
                "organization_id": org_id,
                "name": f"Metodo {str(product.get('name') or product_id)}",
                "code": _slugify(product.get("slug"), fallback=f"metodo-{product_id}"),
                "metadata": {},
                "is_active": True,
            }
        )

    runtime_pillars: list[dict[str, Any]] = []
    for pillar in pillars:
        pillar_id = str(pillar.get("id") or "")
        product_id = str(pillar.get("product_id") or "")
        if not pillar_id or not product_id:
            continue
        metadata = pillar.get("metadata") if isinstance(pillar.get("metadata"), dict) else {}
        runtime_pillars.append(
            {
                "id": f"plr_{pillar_id}",
                "protocol_id": f"prt_{product_id}",
                "name": str(pillar.get("name") or f"Pilar {pillar_id}"),
                "code": _slugify(pillar.get("slug"), fallback=f"pilar-{pillar_id}"),
                "order_index": _to_int(pillar.get("order_index"), 0),
                "metadata": metadata,
                "is_active": bool(pillar.get("is_active", True)),
            }
        )

    runtime_metrics: list[dict[str, Any]] = []
    metrics_by_product: dict[str, list[dict[str, Any]]] = {}

    for metric in metrics:
        metric_id = str(metric.get("id") or "")
        pillar_id = str(metric.get("pillar_id") or "")
        pillar = pillar_by_id.get(pillar_id)
        product_id = str((pillar or {}).get("product_id") or "")
        if not metric_id or not pillar_id or not product_id:
            continue

        metric_row = {
            "id": f"met_{metric_id}",
            "protocol_id": f"prt_{product_id}",
            "pillar_id": f"plr_{pillar_id}",
            "name": str(metric.get("name") or f"Metrica {metric_id}"),
            "code": _slugify(metric.get("slug"), fallback=f"metrica-{metric_id}"),
            "direction": str(metric.get("direction") or "higher_better"),
            "unit": metric.get("unit"),
            "scoring_rules": metric.get("scoring_rules") if metric.get("scoring_rules") is not None else {},
            "score_type": str(metric.get("score_type") or "static"),
            "min_score": _to_int(metric.get("min_score"), 0),
            "max_score": _to_int(metric.get("max_score"), 100),
            "mcv_score": _to_int(metric.get("mcv"), 0),
            "max_basis_score": str(metric.get("max_score_basis") or "MAX_VALUE"),
            "is_active": bool(metric.get("is_active", True)),
        }
        runtime_metrics.append(metric_row)
        metrics_by_product.setdefault(product_id, []).append(metric_row)

    runtime_contacts: list[dict[str, Any]] = []
    runtime_users: list[dict[str, Any]] = []
    runtime_mentors: list[dict[str, Any]] = []
    runtime_students: list[dict[str, Any]] = []
    default_password_hash_by_role = {
        "admin": hash_password(config.default_admin_password),
        "provider": hash_password(config.default_provider_password),
        "client": hash_password(config.default_client_password),
    }

    for row in users:
        source_user_id = str(row.get("id") or "")
        email = str(row.get("email") or "").strip().lower()
        role = str(row.get("role") or "").strip().lower()
        if not source_user_id or not email or role not in {"admin", "provider", "mentor", "client", "student", "aluno"}:
            continue

        internal_role = "provider" if role in {"provider", "mentor"} else "client" if role in {"client", "student", "aluno"} else "admin"
        app_user_role = "mentor" if internal_role == "provider" else internal_role

        source_hash = str(row.get("password_hash") or "").strip() or None
        if source_hash:
            password_hash = source_hash
        elif internal_role == "admin":
            password_hash = default_password_hash_by_role["admin"]
        elif internal_role == "provider":
            password_hash = default_password_hash_by_role["provider"]
        else:
            password_hash = default_password_hash_by_role["client"]

        runtime_contacts.append(
            {
                "id": f"usr_{source_user_id}",
                "full_name": str(row.get("full_name") or email),
                "email": email,
                "role": internal_role,
                "is_active": bool(row.get("is_active", True)),
                "organization_id": row.get("organization_id"),
                "password_hash": password_hash,
                "created_at": _iso(row.get("created_at")),
                "updated_at": _iso(row.get("updated_at")),
            }
        )

        runtime_users.append(
            {
                "id": f"usr_{source_user_id}",
                "email": email,
                "password_hash": password_hash,
                "role": app_user_role,
                "is_active": bool(row.get("is_active", True)),
            }
        )

        if internal_role == "provider":
            provider_org = None
            for enrollment in enrollments:
                if str(enrollment.get("provider_user_id") or "") == source_user_id:
                    provider_org = f"org_{str(enrollment.get('product_id') or '')}"
                    break
            runtime_mentors.append(
                {
                    "id": f"mtr_{source_user_id}",
                    "full_name": str(row.get("full_name") or email),
                    "email": email,
                    "cpf": None,
                    "phone": None,
                    "bio": None,
                    "notes": None,
                    "status": "active" if bool(row.get("is_active", True)) else "inactive",
                    "is_active": bool(row.get("is_active", True)),
                    "organization_id": provider_org,
                    "created_at": _iso(row.get("created_at")),
                    "updated_at": _iso(row.get("updated_at")),
                }
            )

        if internal_role == "client":
            full_name = str(row.get("full_name") or email)
            runtime_students.append(
                {
                    "id": f"std_{source_user_id}",
                    "full_name": full_name,
                    "initials": _initials(full_name),
                    "email": email,
                    "cpf": None,
                    "phone": None,
                    "notes": None,
                    "start_enrollment_date": None,
                    "end_enrollment_date": None,
                    "status": "active" if bool(row.get("is_active", True)) else "inactive",
                    "is_active": bool(row.get("is_active", True)),
                    "created_at": _iso(row.get("created_at")),
                    "updated_at": _iso(row.get("updated_at")),
                }
            )

    runtime_enrollments: list[dict[str, Any]] = []
    runtime_measurements: list[dict[str, Any]] = []
    runtime_checkpoints: list[dict[str, Any]] = []

    measurement_counter = 1
    checkpoint_counter = 1

    for row in enrollments:
        enrollment_id = str(row.get("id") or "")
        provider_user_id = str(row.get("provider_user_id") or "")
        client_user_id = str(row.get("client_user_id") or "")
        product_id = str(row.get("product_id") or "")
        if not enrollment_id or not provider_user_id or not client_user_id or not product_id:
            continue

        days_left = max(_to_int(row.get("days_left"), 0), 0)
        total_days = max(days_left, 90)
        day = max(total_days - days_left, 0)
        progress_score = 0.0 if total_days <= 0 else round(day / total_days, 4)
        engagement_score = 0.55 if str(row.get("status") or "active").lower() == "active" else 0.2
        investment = _to_float(row.get("investment"), 0.0)

        runtime_enrollments.append(
            {
                "id": f"enr_{enrollment_id}",
                "student_id": f"std_{client_user_id}",
                "organization_id": f"org_{product_id}",
                "mentor_id": f"mtr_{provider_user_id}",
                "progress_score": progress_score,
                "engagement_score": engagement_score,
                "urgency_status": "watch" if days_left <= 45 else "normal",
                "day": day,
                "total_days": total_days,
                "days_left": days_left,
                "ltv_cents": int(round(investment * 100)),
                "link_reason": "supabase-sync",
                "source_enrollment_id": None,
                "created_by": "supabase-sync",
                "deactivated_at": None,
                "deactivated_reason": None,
                "deactivated_by": None,
                "reassigned_to_mentor_id": None,
                "is_active": str(row.get("status") or "active").lower() == "active",
                "created_at": _iso(row.get("created_at")),
                "updated_at": _iso(row.get("updated_at")),
            }
        )

        for metric in metrics_by_product.get(product_id, []):
            baseline = float(metric.get("mcv_score") or metric.get("min_score") or 0)
            metric_max = float(metric.get("max_score") or baseline or 100)
            delta = _deterministic_delta(enrollment_id=enrollment_id, metric_id=str(metric.get("id") or "")) * max(metric_max, 1.0)
            current = max(0.0, min(metric_max, baseline + delta))
            projected = max(current, baseline)

            runtime_measurements.append(
                {
                    "id": f"mea_{measurement_counter}",
                    "enrollment_id": f"enr_{enrollment_id}",
                    "metric_id": str(metric.get("id") or ""),
                    "value_baseline": round(baseline, 4),
                    "value_current": round(current, 4),
                    "value_projected": round(projected, 4),
                    "improving_trend": current >= baseline,
                }
            )
            measurement_counter += 1

        checkpoint_status = "green" if days_left > 45 else "yellow" if days_left > 15 else "red"
        runtime_checkpoints.append(
            {
                "id": f"chk_{checkpoint_counter}",
                "enrollment_id": f"enr_{enrollment_id}",
                "week": 1,
                "status": checkpoint_status,
                "label": "Carga inicial",
            }
        )
        checkpoint_counter += 1

    return {
        "contacts_users_v2": {"version": 2, "items": runtime_contacts},
        "users": {"version": 1, "items": runtime_users},
        "organizations": {"version": 1, "items": runtime_organizations},
        "mentors": {"version": 1, "items": runtime_mentors},
        "students": {"version": 1, "items": runtime_students},
        "protocols": {"version": 1, "items": runtime_protocols},
        "pillars": {"version": 1, "items": runtime_pillars},
        "metrics": {"version": 1, "items": runtime_metrics},
        "enrollments": {"version": 1, "items": runtime_enrollments},
        "measurements": {"version": 1, "items": runtime_measurements},
        "checkpoints": {"version": 1, "items": runtime_checkpoints},
        "measurement_overalls": {"version": 1, "items": []},
        "sync_meta": {
            "synced_at": now_iso,
            "source_rows": {
                "users": len(users),
                "organizations": len(source.get("organizations", [])),
                "products": len(products),
                "pillars": len(pillars),
                "metrics": len(metrics),
                "enrollments": len(enrollments),
            },
        },
    }


def _backfill_runtime_indicator_tables(
    *,
    database_url: str,
    payloads: dict[str, dict[str, Any]],
    measurements_repo: Any | None = None,
    checkpoints_repo: Any | None = None,
) -> dict[str, int]:
    started = time.perf_counter()
    logger.info("supabase_sync_backfill_begin")
    if measurements_repo is None and checkpoints_repo is None:
        return _backfill_runtime_indicator_tables_bulk(database_url=database_url, payloads=payloads)

    measurements_store = measurements_repo or PostgresMeasurementRepository(database_url)
    checkpoints_store = checkpoints_repo or PostgresCheckpointRepository(database_url)

    enrollments = payloads.get("enrollments", {}).get("items", [])
    measurements = payloads.get("measurements", {}).get("items", [])
    checkpoints = payloads.get("checkpoints", {}).get("items", [])

    active_enrollment_ids = {
        str(item.get("id") or "")
        for item in enrollments
        if bool(item.get("is_active", False)) and str(item.get("id") or "")
    }

    measurements_by_enrollment: dict[str, list[dict[str, Any]]] = {}
    for row in measurements:
        enrollment_id = str(row.get("enrollment_id") or "")
        if enrollment_id in active_enrollment_ids:
            measurements_by_enrollment.setdefault(enrollment_id, []).append(row)

    checkpoints_by_enrollment: dict[str, list[dict[str, Any]]] = {}
    for row in checkpoints:
        enrollment_id = str(row.get("enrollment_id") or "")
        if enrollment_id in active_enrollment_ids:
            checkpoints_by_enrollment.setdefault(enrollment_id, []).append(row)

    measurement_candidates = 0
    measurement_inserted = 0
    measurement_skipped = 0
    checkpoint_candidates = 0
    checkpoint_inserted = 0
    checkpoint_skipped = 0

    enrollment_ids = sorted(active_enrollment_ids)
    total_enrollments = len(enrollment_ids)

    for idx, enrollment_id in enumerate(enrollment_ids, start=1):
        measurement_rows = measurements_by_enrollment.get(enrollment_id, [])
        checkpoint_rows = checkpoints_by_enrollment.get(enrollment_id, [])

        measurement_result = measurements_store.insert_missing_for_enrollment(enrollment_id, measurement_rows)
        checkpoint_result = checkpoints_store.insert_missing_for_enrollment(enrollment_id, checkpoint_rows)

        measurement_candidates += int(measurement_result.get("candidates", 0) or 0)
        measurement_inserted += int(measurement_result.get("inserted", 0) or 0)
        measurement_skipped += int(measurement_result.get("skipped", 0) or 0)
        checkpoint_candidates += int(checkpoint_result.get("candidates", 0) or 0)
        checkpoint_inserted += int(checkpoint_result.get("inserted", 0) or 0)
        checkpoint_skipped += int(checkpoint_result.get("skipped", 0) or 0)
        if idx % 25 == 0 or idx == total_enrollments:
            logger.info(
                "supabase_sync_backfill_progress processed=%s total=%s measurement_inserted=%s checkpoint_inserted=%s",
                idx,
                total_enrollments,
                measurement_inserted,
                checkpoint_inserted,
            )

    result = {
        "active_enrollments": len(active_enrollment_ids),
        "measurement_candidates": measurement_candidates,
        "measurement_inserted": measurement_inserted,
        "measurement_skipped": measurement_skipped,
        "checkpoint_candidates": checkpoint_candidates,
        "checkpoint_inserted": checkpoint_inserted,
        "checkpoint_skipped": checkpoint_skipped,
    }
    logger.info(
        "supabase_sync_backfill_completed active_enrollments=%s measurement_inserted=%s checkpoint_inserted=%s elapsed_ms=%s",
        result["active_enrollments"],
        result["measurement_inserted"],
        result["checkpoint_inserted"],
        int((time.perf_counter() - started) * 1000),
    )
    return result


def _backfill_runtime_indicator_tables_bulk(*, database_url: str, payloads: dict[str, dict[str, Any]]) -> dict[str, int]:
    started = time.perf_counter()
    measurements_store = PostgresMeasurementRepository(database_url)
    checkpoints_store = PostgresCheckpointRepository(database_url)

    enrollments = payloads.get("enrollments", {}).get("items", [])
    measurements = payloads.get("measurements", {}).get("items", [])
    checkpoints = payloads.get("checkpoints", {}).get("items", [])

    active_enrollment_ids = sorted(
        {
            str(item.get("id") or "")
            for item in enrollments
            if bool(item.get("is_active", False)) and str(item.get("id") or "")
        }
    )
    active_enrollment_set = set(active_enrollment_ids)

    measurement_params: list[tuple[Any, ...]] = []
    for row in measurements:
        enrollment_id = str(row.get("enrollment_id") or "")
        if enrollment_id not in active_enrollment_set:
            continue
        measurement_params.append(
            (
                str(row.get("id") or f"mea_{uuid4().hex}"),
                enrollment_id,
                str(row["metric_id"]),
                float(row["value_baseline"]),
                float(row["value_current"]),
                None if row.get("value_projected") is None else float(row["value_projected"]),
                row.get("improving_trend"),
            )
        )

    checkpoint_params: list[tuple[Any, ...]] = []
    for row in checkpoints:
        enrollment_id = str(row.get("enrollment_id") or "")
        if enrollment_id not in active_enrollment_set:
            continue
        checkpoint_params.append(
            (
                str(row.get("id") or f"chk_{uuid4().hex}"),
                enrollment_id,
                int(row["week"]),
                str(row["status"]),
                row.get("label"),
            )
        )

    measurement_candidates = len(measurement_params)
    checkpoint_candidates = len(checkpoint_params)
    measurement_inserted = 0
    checkpoint_inserted = 0

    with _connect(database_url) as conn:
        with conn.cursor() as cur:
            measurements_store._ensure_table(cur)
            checkpoints_store._ensure_table(cur)

            # Fast-path: when runtime tables are already fully backfilled for active enrollments.
            if active_enrollment_ids:
                cur.execute(
                    f"SELECT COUNT(*) FROM {PostgresMeasurementRepository._TABLE} WHERE enrollment_id = ANY(%s)",
                    (active_enrollment_ids,),
                )
                existing_measurements = int((cur.fetchone() or [0])[0] or 0)
                cur.execute(
                    f"SELECT COUNT(*) FROM {PostgresCheckpointRepository._TABLE} WHERE enrollment_id = ANY(%s)",
                    (active_enrollment_ids,),
                )
                existing_checkpoints = int((cur.fetchone() or [0])[0] or 0)
                if (
                    existing_measurements >= measurement_candidates
                    and existing_checkpoints >= checkpoint_candidates
                ):
                    conn.commit()
                    elapsed_ms = int((time.perf_counter() - started) * 1000)
                    logger.info(
                        "supabase_sync_backfill_fastpath active_enrollments=%s existing_measurements=%s existing_checkpoints=%s elapsed_ms=%s",
                        len(active_enrollment_ids),
                        existing_measurements,
                        existing_checkpoints,
                        elapsed_ms,
                    )
                    return {
                        "active_enrollments": len(active_enrollment_ids),
                        "measurement_candidates": measurement_candidates,
                        "measurement_inserted": 0,
                        "measurement_skipped": measurement_candidates,
                        "checkpoint_candidates": checkpoint_candidates,
                        "checkpoint_inserted": 0,
                        "checkpoint_skipped": checkpoint_candidates,
                    }

            if measurement_params:
                cur.executemany(
                    f"""
                    INSERT INTO {PostgresMeasurementRepository._TABLE} (
                        id, enrollment_id, metric_id, value_baseline, value_current, value_projected, improving_trend
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (enrollment_id, metric_id) DO NOTHING
                    """,
                    measurement_params,
                )
                measurement_inserted = int(cur.rowcount or 0)

            if checkpoint_params:
                cur.executemany(
                    f"""
                    INSERT INTO {PostgresCheckpointRepository._TABLE} (id, enrollment_id, week, status, label)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (enrollment_id, week) DO NOTHING
                    """,
                    checkpoint_params,
                )
                checkpoint_inserted = int(cur.rowcount or 0)

        conn.commit()

    result = {
        "active_enrollments": len(active_enrollment_ids),
        "measurement_candidates": measurement_candidates,
        "measurement_inserted": measurement_inserted,
        "measurement_skipped": max(measurement_candidates - measurement_inserted, 0),
        "checkpoint_candidates": checkpoint_candidates,
        "checkpoint_inserted": checkpoint_inserted,
        "checkpoint_skipped": max(checkpoint_candidates - checkpoint_inserted, 0),
    }
    logger.info(
        "supabase_sync_backfill_completed_bulk active_enrollments=%s measurement_inserted=%s checkpoint_inserted=%s elapsed_ms=%s",
        result["active_enrollments"],
        result["measurement_inserted"],
        result["checkpoint_inserted"],
        int((time.perf_counter() - started) * 1000),
    )
    return result


def _write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _build_runtime_clients_payload(source_rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    clients: list[dict[str, Any]] = []
    for organization in source_rows.get("organizations", []):
        organization_id = str(organization.get("id") or "").strip()
        if not organization_id:
            continue
        name = str(organization.get("name") or "").strip() or f"Cliente {organization_id}"
        brand_name = str(organization.get("brand_name") or "").strip() or name
        clients.append(
            {
                "id": f"cli_{organization_id}",
                "name": name,
                "brand_name": brand_name,
                "cnpj": "",
                "slug": str(organization.get("slug") or "").strip() or f"cliente-{organization_id}",
                "status": str(organization.get("status") or "active"),
                "is_active": bool(organization.get("is_active", True)),
                "timezone": "America/Sao_Paulo",
                "currency": "BRL",
                "notes": None,
                "created_at": _iso(organization.get("created_at")),
                "updated_at": _iso(organization.get("updated_at")),
            }
        )
    return {"version": 1, "items": clients}


def sync_runtime_stores_from_supabase(config: SupabaseSyncConfig) -> SupabaseSyncResult:
    started = time.perf_counter()
    logger.info("supabase_sync_begin")
    source_rows = _fetch_source_rows(config.database_url)
    logger.info("supabase_sync_build_payloads_begin")
    payloads = _build_runtime_payloads(source_rows, config)
    payloads["clients"] = _build_runtime_clients_payload(source_rows)
    logger.info(
        "supabase_sync_build_payloads_completed clients=%s contacts=%s users=%s organizations=%s mentors=%s students=%s protocols=%s pillars=%s metrics=%s enrollments=%s measurements=%s checkpoints=%s",
        len(payloads["clients"]["items"]),
        len(payloads["contacts_users_v2"]["items"]),
        len(payloads["users"]["items"]),
        len(payloads["organizations"]["items"]),
        len(payloads["mentors"]["items"]),
        len(payloads["students"]["items"]),
        len(payloads["protocols"]["items"]),
        len(payloads["pillars"]["items"]),
        len(payloads["metrics"]["items"]),
        len(payloads["enrollments"]["items"]),
        len(payloads["measurements"]["items"]),
        len(payloads["checkpoints"]["items"]),
    )
    runtime_backfill = _backfill_runtime_indicator_tables(database_url=config.database_url, payloads=payloads)

    stores: dict[str, Path] = {
        "clients": resolve_store_path("CLIENT_STORE_PATH", "clients.json"),
        "contacts_users_v2": resolve_store_path("CONTACT_USER_STORE_PATH", "contacts_users_v2.json"),
        "users": resolve_store_path("USER_STORE_PATH", "users.json"),
        "organizations": resolve_store_path("ORG_STORE_PATH", "organizations.json"),
        "mentors": resolve_store_path("MENTOR_STORE_PATH", "mentors.json"),
        "students": resolve_store_path("STUDENT_STORE_PATH", "students.json"),
        "protocols": resolve_store_path("PROTOCOL_STORE_PATH", "protocols.json"),
        "pillars": resolve_store_path("PILLAR_STORE_PATH", "pillars.json"),
        "metrics": resolve_store_path("METRIC_STORE_PATH", "metrics.json"),
        "enrollments": resolve_store_path("ENROLLMENT_STORE_PATH", "enrollments.json"),
        "measurements": resolve_store_path("MEASUREMENT_STORE_PATH", "measurements.json"),
        "checkpoints": resolve_store_path("CHECKPOINT_STORE_PATH", "checkpoints.json"),
        "measurement_overalls": resolve_store_path("MEASUREMENT_OVERALL_STORE_PATH", "measurement_overalls.json"),
    }

    for store_name, path in stores.items():
        _write_payload(path, payloads[store_name])

    report_path = resolve_store_path("SUPABASE_RUNTIME_SYNC_REPORT_PATH", "supabase_runtime_sync_report.json")
    _write_payload(
        report_path,
        {
            **payloads["sync_meta"],
            "runtime_backfill": runtime_backfill,
            "targets": {name: str(path) for name, path in stores.items()},
            "written_items": {name: len(payloads[name]["items"]) for name in stores},
        },
    )

    counters = {name: len(payloads[name]["items"]) for name in stores}
    counters.update(
        {
            "runtime_backfill_active_enrollments": int(runtime_backfill["active_enrollments"]),
            "runtime_backfill_measurement_candidates": int(runtime_backfill["measurement_candidates"]),
            "runtime_backfill_measurement_inserted": int(runtime_backfill["measurement_inserted"]),
            "runtime_backfill_measurement_skipped": int(runtime_backfill["measurement_skipped"]),
            "runtime_backfill_checkpoint_candidates": int(runtime_backfill["checkpoint_candidates"]),
            "runtime_backfill_checkpoint_inserted": int(runtime_backfill["checkpoint_inserted"]),
            "runtime_backfill_checkpoint_skipped": int(runtime_backfill["checkpoint_skipped"]),
        }
    )

    result = SupabaseSyncResult(
        stores=stores,
        counters=counters,
    )
    logger.info(
        "supabase_sync_completed total_elapsed_ms=%s runtime_backfill_active_enrollments=%s",
        int((time.perf_counter() - started) * 1000),
        counters["runtime_backfill_active_enrollments"],
    )
    return result


__all__ = [
    "SupabaseSyncConfig",
    "SupabaseSyncResult",
    "sync_runtime_stores_from_supabase",
    "_build_runtime_payloads",
    "_backfill_runtime_indicator_tables",
]
