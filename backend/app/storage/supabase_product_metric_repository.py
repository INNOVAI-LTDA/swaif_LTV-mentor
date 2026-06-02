from __future__ import annotations

from typing import Any

from app.config.runtime import get_supabase_db_url

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


class SupabaseProductMetricRepository:
    def __init__(self, database_url: str | None = None) -> None:
        self._database_url = (database_url or get_supabase_db_url()).strip()
        if not self._database_url:
            raise RuntimeError("SUPABASE_DB_URL is required for SupabaseProductMetricRepository.")
        if psycopg is None:
            raise RuntimeError("SUPABASE_DB_URL is configured but psycopg is not installed.")

    def list_metric_tree_by_product(self, product_id: str) -> list[dict[str, Any]]:
        query = """
            SELECT
              pp.id AS pillar_id,
              pp.name AS pillar_name,
              pp.slug AS pillar_slug,
              pp.order_index AS pillar_order_index,
              pm.id AS metric_id,
              pm.name AS metric_name,
              pm.slug AS metric_slug,
              pm.direction,
              pm.unit,
              pm.scoring_rules,
              pm.score_type,
              pm.min_score,
              pm.max_score,
              pm.max_score_basis,
              pm.mcv
            FROM deva_accmed_product_pillars pp
            JOIN deva_accmed_product_metrics pm
              ON pm.pillar_id = pp.id
             AND pm.is_active = true
            WHERE pp.product_id = %s
              AND pp.is_active = true
            ORDER BY pp.order_index ASC, pm.id ASC;
        """
        with psycopg.connect(self._database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (product_id,))
                columns = [column[0] for column in (cur.description or ())]
                rows = [dict(zip(columns, row)) for row in cur.fetchall()]

        pillars: list[dict[str, Any]] = []
        by_pillar_id: dict[str, dict[str, Any]] = {}

        for row in rows:
            pillar_id = str(row.get("pillar_id") or "")
            pillar = by_pillar_id.get(pillar_id)
            if pillar is None:
                pillar = {
                    "id": pillar_id,
                    "name": str(row.get("pillar_name") or ""),
                    "slug": str(row.get("pillar_slug") or ""),
                    "orderIndex": row.get("pillar_order_index"),
                    "metrics": [],
                }
                by_pillar_id[pillar_id] = pillar
                pillars.append(pillar)

            pillar["metrics"].append(
                {
                    "id": str(row.get("metric_id") or ""),
                    "name": str(row.get("metric_name") or ""),
                    "slug": str(row.get("metric_slug") or ""),
                    "direction": row.get("direction"),
                    "unit": row.get("unit"),
                    "scoringRules": row.get("scoring_rules"),
                    "scoreType": row.get("score_type"),
                    "minScore": row.get("min_score"),
                    "maxScore": row.get("max_score"),
                    "maxScoreBasis": row.get("max_score_basis"),
                    "mcv": row.get("mcv"),
                }
            )

        return pillars
