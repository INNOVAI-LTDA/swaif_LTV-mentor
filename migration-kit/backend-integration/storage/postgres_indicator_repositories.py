from __future__ import annotations

from contextlib import contextmanager
from typing import Any
from uuid import uuid4

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


def _rows_from_cursor(cursor: Any) -> list[dict[str, Any]]:
    columns = [column[0] for column in (cursor.description or ())]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


class _PostgresBaseRepository:
    runtime_backend = "postgres"

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    @contextmanager
    def _cursor(self) -> Any:
        if psycopg is None:
            raise RuntimeError("psycopg is not installed.")
        with psycopg.connect(self._database_url) as conn:
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

