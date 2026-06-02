from __future__ import annotations

from typing import Any

from app.config.runtime import get_supabase_db_url

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


class SupabaseProviderHierarchyRepository:
    def __init__(self, database_url: str | None = None) -> None:
        self._database_url = (database_url or get_supabase_db_url()).strip()
        if not self._database_url:
            raise RuntimeError("SUPABASE_DB_URL is required for SupabaseProviderHierarchyRepository.")
        if psycopg is None:
            raise RuntimeError("SUPABASE_DB_URL is configured but psycopg is not installed.")

    def list_active_provider_hierarchy(self, provider_user_id: str) -> list[dict[str, Any]]:
        query = """
            SELECT
              e.id AS enrollment_id,
              e.status AS enrollment_status,
              e.start_day,
              e.days_left,
              e.investment,
              e.decision_matrix_status,

              provider.id AS provider_id,
              provider.full_name AS provider_name,
              provider.email AS provider_email,
              provider.organization_id AS provider_organization_id,

              client.id AS client_id,
              client.full_name AS client_name,
              client.email AS client_email,

              p.id AS product_id,
              p.name AS product_name,
              p.slug AS product_slug,
              p.category AS product_category,

              o.id AS organization_id,
              o.name AS organization_name,
              o.slug AS organization_slug

            FROM deva_accmed_enrollments e
            JOIN deva_accmed_users provider
              ON provider.id = e.provider_user_id
             AND provider.role = 'provider'
             AND provider.is_active = true
            JOIN deva_accmed_users client
              ON client.id = e.client_user_id
             AND client.role = 'client'
             AND client.is_active = true
            JOIN deva_accmed_products p
              ON p.id = e.product_id
            JOIN deva_accmed_organizations o
              ON o.id = p.organization_id
            WHERE e.provider_user_id = %s
              AND e.status = 'active'
            ORDER BY client.full_name ASC, e.updated_at DESC;
        """
        with psycopg.connect(self._database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (provider_user_id,))
                columns = [column[0] for column in (cur.description or ())]
                return [dict(zip(columns, row)) for row in cur.fetchall()]
