#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.operations.sync_runtime_stores_from_supabase import (
    SupabaseSyncConfig,
    sync_runtime_stores_from_supabase,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sync Supabase/Postgres tables into local JSON runtime stores used by backend repositories."
        )
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("SUPABASE_DB_URL"),
        help="Postgres URL. Defaults to SUPABASE_DB_URL env var.",
    )
    parser.add_argument(
        "--default-admin-password",
        default=os.getenv("SUPABASE_SYNC_DEFAULT_ADMIN_PASSWORD", "admin123"),
        help="Fallback plaintext used to generate admin password_hash when DB row has no password_hash.",
    )
    parser.add_argument(
        "--default-provider-password",
        default=os.getenv("SUPABASE_SYNC_DEFAULT_PROVIDER_PASSWORD", "mentor123"),
        help="Fallback plaintext used to generate provider password_hash when DB row has no password_hash.",
    )
    parser.add_argument(
        "--default-client-password",
        default=os.getenv("SUPABASE_SYNC_DEFAULT_CLIENT_PASSWORD", os.getenv("APP_DEFAULT_STUDENT_PASSWORD", "aluno_accmed")),
        help="Fallback plaintext used to generate client password_hash when DB row has no password_hash.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.database_url:
        raise SystemExit("Missing database URL. Provide --database-url or SUPABASE_DB_URL.")

    result = sync_runtime_stores_from_supabase(
        SupabaseSyncConfig(
            database_url=args.database_url,
            default_admin_password=args.default_admin_password,
            default_provider_password=args.default_provider_password,
            default_client_password=args.default_client_password,
        )
    )

    print("Supabase runtime sync summary")
    for name, count in sorted(result.counters.items()):
        print(f"- {name}: {count} items")
    for name, path in sorted(result.stores.items()):
        print(f"- {name}_path: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
