from __future__ import annotations

from typing import Any

from app.config.runtime import get_supabase_db_url

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


class SupabaseRuntimeMeasurementRepository:
    def __init__(self, database_url: str | None = None) -> None:
        self._database_url = (database_url or get_supabase_db_url()).strip()
        if not self._database_url:
            raise RuntimeError("SUPABASE_DB_URL is required for SupabaseRuntimeMeasurementRepository.")
        if psycopg is None:
            raise RuntimeError("SUPABASE_DB_URL is configured but psycopg is not installed.")

    def list_by_enrollment(self, enrollment_id: str) -> list[dict[str, Any]]:
        query = """
            SELECT
              id,
              enrollment_id,
              metric_id,
              value_baseline,
              value_current,
              value_projected,
              improving_trend,
              created_at,
              updated_at
            FROM deva_accmed_runtime_measurements
            WHERE enrollment_id = %s
            ORDER BY metric_id ASC;
        """
        with psycopg.connect(self._database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (enrollment_id,))
                columns = [column[0] for column in (cur.description or ())]
                rows = [dict(zip(columns, row)) for row in cur.fetchall()]

        result: list[dict[str, Any]] = []
        for row in rows:
            result.append(
                {
                    "id": str(row.get("id") or ""),
                    "enrollment_id": str(row.get("enrollment_id") or ""),
                    "metric_id": str(row.get("metric_id") or ""),
                    "value_baseline": row.get("value_baseline"),
                    "value_current": row.get("value_current"),
                    "value_projected": row.get("value_projected"),
                    "improving_trend": row.get("improving_trend"),
                    "created_at": row.get("created_at"),
                    "updated_at": row.get("updated_at"),
                }
            )
        return result
