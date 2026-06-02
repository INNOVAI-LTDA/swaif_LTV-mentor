from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any
from uuid import uuid4

from app.config.runtime import get_supabase_db_connect_timeout_seconds

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


def _connect(database_url: str) -> Any:
    if psycopg is None:
        raise RuntimeError("psycopg is not installed.")
    # Supabase shared pooler (transaction mode) is not compatible with prepared statements.
    return psycopg.connect(
        database_url,
        prepare_threshold=None,
        connect_timeout=get_supabase_db_connect_timeout_seconds(),
    )


def _rows_from_cursor(cursor: Any) -> list[dict[str, Any]]:
    columns = [column[0] for column in (cursor.description or ())]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


class _PostgresBaseRepository:
    runtime_backend = "postgres"

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    @contextmanager
    def _cursor(self) -> Any:
        with _connect(self._database_url) as conn:
            with conn.cursor() as cur:
                yield cur
            conn.commit()


class PostgresMeasurementRepository(_PostgresBaseRepository):
    _TABLE = "deva_accmed_runtime_measurements"

    def _ensure_table(self, cursor: Any) -> None:
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self._TABLE} (
                id TEXT PRIMARY KEY,
                enrollment_id TEXT NOT NULL,
                metric_id TEXT NOT NULL,
                value_baseline DOUBLE PRECISION NOT NULL,
                value_current DOUBLE PRECISION NOT NULL,
                value_projected DOUBLE PRECISION NULL,
                improving_trend BOOLEAN NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{self._TABLE}_enrollment ON {self._TABLE} (enrollment_id)")
        cursor.execute(
            f"CREATE UNIQUE INDEX IF NOT EXISTS idx_{self._TABLE}_enrollment_metric_unique ON {self._TABLE} (enrollment_id, metric_id)"
        )

    def list_measurements(self) -> list[dict[str, Any]]:
        with self._cursor() as cur:
            self._ensure_table(cur)
            cur.execute(
                f"""
                SELECT id, enrollment_id, metric_id, value_baseline, value_current, value_projected, improving_trend
                FROM {self._TABLE}
                """
            )
            return _rows_from_cursor(cur)

    def list_by_enrollment(self, enrollment_id: str) -> list[dict[str, Any]]:
        with self._cursor() as cur:
            self._ensure_table(cur)
            cur.execute(
                f"""
                SELECT id, enrollment_id, metric_id, value_baseline, value_current, value_projected, improving_trend
                FROM {self._TABLE}
                WHERE enrollment_id = %s
                ORDER BY created_at ASC, id ASC
                """,
                (enrollment_id,),
            )
            return _rows_from_cursor(cur)

    def get_by_id(self, measurement_id: str) -> dict[str, Any] | None:
        with self._cursor() as cur:
            self._ensure_table(cur)
            cur.execute(
                f"""
                SELECT id, enrollment_id, metric_id, value_baseline, value_current, value_projected, improving_trend
                FROM {self._TABLE}
                WHERE id = %s
                LIMIT 1
                """,
                (measurement_id,),
            )
            rows = _rows_from_cursor(cur)
            return rows[0] if rows else None

    def update_value_current(self, measurement_id: str, value_current: float) -> dict[str, Any]:
        with self._cursor() as cur:
            self._ensure_table(cur)
            cur.execute(
                f"""
                UPDATE {self._TABLE}
                SET value_current = %s, updated_at = now()
                WHERE id = %s
                RETURNING id, enrollment_id, metric_id, value_baseline, value_current, value_projected, improving_trend
                """,
                (float(value_current), measurement_id),
            )
            rows = _rows_from_cursor(cur)
            if not rows:
                raise ValueError("measurement not found")
            return rows[0]

    def replace_for_enrollment(self, enrollment_id: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        with self._cursor() as cur:
            self._ensure_table(cur)
            cur.execute(f"DELETE FROM {self._TABLE} WHERE enrollment_id = %s", (enrollment_id,))

            created: list[dict[str, Any]] = []
            for row in rows:
                record = {
                    "id": f"mea_{uuid4().hex}",
                    "enrollment_id": enrollment_id,
                    "metric_id": str(row["metric_id"]),
                    "value_baseline": float(row["value_baseline"]),
                    "value_current": float(row["value_current"]),
                    "value_projected": None if row.get("value_projected") is None else float(row["value_projected"]),
                    "improving_trend": row.get("improving_trend"),
                }
                cur.execute(
                    f"""
                    INSERT INTO {self._TABLE} (
                        id, enrollment_id, metric_id, value_baseline, value_current, value_projected, improving_trend
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        record["id"],
                        record["enrollment_id"],
                        record["metric_id"],
                        record["value_baseline"],
                        record["value_current"],
                        record["value_projected"],
                        record["improving_trend"],
                    ),
                )
                created.append(record)
            return created

    def insert_missing_for_enrollment(self, enrollment_id: str, rows: list[dict[str, Any]]) -> dict[str, int]:
        with self._cursor() as cur:
            self._ensure_table(cur)
            inserted = 0
            for row in rows:
                record_id = str(row.get("id") or f"mea_{uuid4().hex}")
                cur.execute(
                    f"""
                    INSERT INTO {self._TABLE} (
                        id, enrollment_id, metric_id, value_baseline, value_current, value_projected, improving_trend
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (enrollment_id, metric_id) DO NOTHING
                    """,
                    (
                        record_id,
                        enrollment_id,
                        str(row["metric_id"]),
                        float(row["value_baseline"]),
                        float(row["value_current"]),
                        None if row.get("value_projected") is None else float(row["value_projected"]),
                        row.get("improving_trend"),
                    ),
                )
                inserted += int(cur.rowcount or 0)
            candidates = len(rows)
            return {
                "candidates": candidates,
                "inserted": inserted,
                "skipped": max(candidates - inserted, 0),
            }


class PostgresCheckpointRepository(_PostgresBaseRepository):
    _TABLE = "deva_accmed_runtime_checkpoints"

    def _ensure_table(self, cursor: Any) -> None:
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self._TABLE} (
                id TEXT PRIMARY KEY,
                enrollment_id TEXT NOT NULL,
                week INTEGER NOT NULL,
                status TEXT NOT NULL,
                label TEXT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{self._TABLE}_enrollment ON {self._TABLE} (enrollment_id)")
        cursor.execute(
            f"CREATE UNIQUE INDEX IF NOT EXISTS idx_{self._TABLE}_enrollment_week_unique ON {self._TABLE} (enrollment_id, week)"
        )

    def list_checkpoints(self) -> list[dict[str, Any]]:
        with self._cursor() as cur:
            self._ensure_table(cur)
            cur.execute(f"SELECT id, enrollment_id, week, status, label FROM {self._TABLE}")
            return _rows_from_cursor(cur)

    def list_by_enrollment(self, enrollment_id: str) -> list[dict[str, Any]]:
        with self._cursor() as cur:
            self._ensure_table(cur)
            cur.execute(
                f"""
                SELECT id, enrollment_id, week, status, label
                FROM {self._TABLE}
                WHERE enrollment_id = %s
                ORDER BY week ASC, created_at ASC, id ASC
                """,
                (enrollment_id,),
            )
            return _rows_from_cursor(cur)

    def replace_for_enrollment(self, enrollment_id: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        with self._cursor() as cur:
            self._ensure_table(cur)
            cur.execute(f"DELETE FROM {self._TABLE} WHERE enrollment_id = %s", (enrollment_id,))

            created: list[dict[str, Any]] = []
            for row in rows:
                record = {
                    "id": f"chk_{uuid4().hex}",
                    "enrollment_id": enrollment_id,
                    "week": int(row["week"]),
                    "status": str(row["status"]),
                    "label": row.get("label"),
                }
                cur.execute(
                    f"""
                    INSERT INTO {self._TABLE} (id, enrollment_id, week, status, label)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        record["id"],
                        record["enrollment_id"],
                        record["week"],
                        record["status"],
                        record["label"],
                    ),
                )
                created.append(record)
            return created

    def insert_missing_for_enrollment(self, enrollment_id: str, rows: list[dict[str, Any]]) -> dict[str, int]:
        with self._cursor() as cur:
            self._ensure_table(cur)
            inserted = 0
            for row in rows:
                record_id = str(row.get("id") or f"chk_{uuid4().hex}")
                cur.execute(
                    f"""
                    INSERT INTO {self._TABLE} (id, enrollment_id, week, status, label)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (enrollment_id, week) DO NOTHING
                    """,
                    (
                        record_id,
                        enrollment_id,
                        int(row["week"]),
                        str(row["status"]),
                        row.get("label"),
                    ),
                )
                inserted += int(cur.rowcount or 0)
            candidates = len(rows)
            return {
                "candidates": candidates,
                "inserted": inserted,
                "skipped": max(candidates - inserted, 0),
            }


class PostgresMeasurementHistoryRepository(_PostgresBaseRepository):
    _TABLE = "deva_accmed_runtime_measurement_history"

    def _ensure_table(self, cursor: Any) -> None:
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self._TABLE} (
                id TEXT PRIMARY KEY,
                measurement_id TEXT NOT NULL,
                enrollment_id TEXT NOT NULL,
                metric_id TEXT NOT NULL,
                actor_user_id TEXT NULL,
                actor_role TEXT NULL,
                value_absolute_before DOUBLE PRECISION NULL,
                value_absolute_after DOUBLE PRECISION NULL,
                value_relative_before DOUBLE PRECISION NULL,
                value_relative_after DOUBLE PRECISION NULL,
                rule_version TEXT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{self._TABLE}_measurement ON {self._TABLE} (measurement_id)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{self._TABLE}_enrollment ON {self._TABLE} (enrollment_id)")

    def append_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._cursor() as cur:
            self._ensure_table(cur)
            record = {
                "id": str(payload.get("id") or f"meh_{uuid4().hex}"),
                "measurement_id": str(payload["measurement_id"]),
                "enrollment_id": str(payload["enrollment_id"]),
                "metric_id": str(payload["metric_id"]),
                "actor_user_id": str(payload.get("actor_user_id") or "") or None,
                "actor_role": str(payload.get("actor_role") or "") or None,
                "value_absolute_before": payload.get("value_absolute_before"),
                "value_absolute_after": payload.get("value_absolute_after"),
                "value_relative_before": payload.get("value_relative_before"),
                "value_relative_after": payload.get("value_relative_after"),
                "rule_version": str(payload.get("rule_version") or "") or None,
            }
            cur.execute(
                f"""
                INSERT INTO {self._TABLE} (
                    id,
                    measurement_id,
                    enrollment_id,
                    metric_id,
                    actor_user_id,
                    actor_role,
                    value_absolute_before,
                    value_absolute_after,
                    value_relative_before,
                    value_relative_after,
                    rule_version
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING
                    id,
                    measurement_id,
                    enrollment_id,
                    metric_id,
                    actor_user_id,
                    actor_role,
                    value_absolute_before,
                    value_absolute_after,
                    value_relative_before,
                    value_relative_after,
                    rule_version,
                    created_at
                """,
                (
                    record["id"],
                    record["measurement_id"],
                    record["enrollment_id"],
                    record["metric_id"],
                    record["actor_user_id"],
                    record["actor_role"],
                    record["value_absolute_before"],
                    record["value_absolute_after"],
                    record["value_relative_before"],
                    record["value_relative_after"],
                    record["rule_version"],
                ),
            )
            rows = _rows_from_cursor(cur)
            return rows[0]


class PostgresAnalyticalHistoryRepository(_PostgresBaseRepository):
    _TABLE = "deva_accmed_runtime_analytical_history"

    def _ensure_table(self, cursor: Any) -> None:
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self._TABLE} (
                id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                enrollment_id TEXT NULL,
                product_id TEXT NULL,
                pillar_id TEXT NULL,
                scoring_rule_version TEXT NULL,
                projection_formula_version TEXT NULL,
                source_effective_at TIMESTAMPTZ NULL,
                payload_json JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{self._TABLE}_event_type ON {self._TABLE} (event_type)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{self._TABLE}_enrollment ON {self._TABLE} (enrollment_id)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{self._TABLE}_product ON {self._TABLE} (product_id)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{self._TABLE}_pillar ON {self._TABLE} (pillar_id)")

    def append_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._cursor() as cur:
            self._ensure_table(cur)
            record = {
                "id": str(payload.get("id") or f"anh_{uuid4().hex}"),
                "event_type": str(payload.get("event_type") or "unknown"),
                "enrollment_id": str(payload.get("enrollment_id") or "") or None,
                "product_id": str(payload.get("product_id") or "") or None,
                "pillar_id": str(payload.get("pillar_id") or "") or None,
                "scoring_rule_version": str(payload.get("scoring_rule_version") or "") or None,
                "projection_formula_version": str(payload.get("projection_formula_version") or "") or None,
                "source_effective_at": payload.get("source_effective_at"),
                "payload_json": payload.get("payload") if isinstance(payload.get("payload"), dict) else {},
            }
            cur.execute(
                f"""
                INSERT INTO {self._TABLE} (
                    id,
                    event_type,
                    enrollment_id,
                    product_id,
                    pillar_id,
                    scoring_rule_version,
                    projection_formula_version,
                    source_effective_at,
                    payload_json
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                RETURNING
                    id,
                    event_type,
                    enrollment_id,
                    product_id,
                    pillar_id,
                    scoring_rule_version,
                    projection_formula_version,
                    source_effective_at,
                    payload_json,
                    created_at
                """,
                (
                    record["id"],
                    record["event_type"],
                    record["enrollment_id"],
                    record["product_id"],
                    record["pillar_id"],
                    record["scoring_rule_version"],
                    record["projection_formula_version"],
                    record["source_effective_at"],
                    json.dumps(record["payload_json"]),
                ),
            )
            rows = _rows_from_cursor(cur)
            return rows[0]
