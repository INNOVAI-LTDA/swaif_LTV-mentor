#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None

ROOT = Path(__file__).resolve().parents[3]
INPUT_PATH = ROOT / "backend" / "data" / "contacts_users_v2.json"
REPORT_PATH = ROOT / "backend" / "data" / "contacts_users_v2_supabase_import_report.json"


@dataclass(frozen=True)
class UserRow:
    id: str
    email: str
    role: str
    full_name: str
    is_active: bool
    organization_id: str | None
    created_at: str
    updated_at: str
    password_hash: str | None


@dataclass
class ImportStats:
    inserted: int = 0
    updated: int = 0
    rejected: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import contacts_users_v2 into Supabase (Postgres).")
    parser.add_argument("--dry-run", action="store_true", help="Validate and simulate import without writing to DB.")
    parser.add_argument("--apply", action="store_true", help="Apply upsert into DB.")
    parser.add_argument(
        "--database-url",
        default=os.getenv("SUPABASE_DB_URL"),
        help="Postgres URL. Defaults to SUPABASE_DB_URL env var.",
    )
    return parser.parse_args()


def load_rows() -> list[UserRow]:
    payload = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    items = payload.get("items", [])
    rows: list[UserRow] = []
    for item in items:
        rows.append(
            UserRow(
                id=str(item["id"]),
                email=str(item["email"]),
                role=str(item["role"]),
                full_name=str(item["full_name"]),
                is_active=bool(item["is_active"]),
                organization_id=item.get("organization_id"),
                created_at=str(item["created_at"]),
                updated_at=str(item["updated_at"]),
                password_hash=item.get("password_hash"),
            )
        )
    return rows


def validate_rows(rows: list[UserRow]) -> tuple[list[UserRow], list[dict[str, Any]]]:
    rejected: list[dict[str, Any]] = []
    valid: list[UserRow] = []
    ids: Counter[str] = Counter()
    emails_lower: Counter[str] = Counter()

    for row in rows:
        ids[row.id] += 1
        emails_lower[row.email.strip().lower()] += 1

    for row in rows:
        reasons: list[str] = []
        if not row.id.strip():
            reasons.append("missing_id")
        if not row.email.strip():
            reasons.append("missing_email")
        if ids[row.id] > 1:
            reasons.append("duplicate_id_in_input")
        if emails_lower[row.email.strip().lower()] > 1:
            reasons.append("duplicate_email_in_input_case_insensitive")
        if reasons:
            rejected.append({"id": row.id, "email": row.email, "reasons": reasons})
            continue
        valid.append(row)

    return valid, rejected


def apply_upsert(database_url: str, rows: list[UserRow]) -> ImportStats:
    if psycopg is None:
        raise RuntimeError("psycopg is not installed. Install dependency before --apply.")

    stats = ImportStats()
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            for row in rows:
                cur.execute(
                    "SELECT id FROM contacts_users_v2 WHERE lower(email) = lower(%s) AND id <> %s",
                    (row.email, row.id),
                )
                email_conflict = cur.fetchone()
                if email_conflict:
                    stats.rejected += 1
                    continue

                cur.execute("SELECT 1 FROM contacts_users_v2 WHERE id = %s", (row.id,))
                exists = cur.fetchone() is not None

                cur.execute(
                    """
                    INSERT INTO contacts_users_v2 (
                        id, email, role, full_name, is_active, organization_id, created_at, updated_at, password_hash
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        email = EXCLUDED.email,
                        role = EXCLUDED.role,
                        full_name = EXCLUDED.full_name,
                        is_active = EXCLUDED.is_active,
                        organization_id = EXCLUDED.organization_id,
                        created_at = EXCLUDED.created_at,
                        updated_at = EXCLUDED.updated_at,
                        password_hash = EXCLUDED.password_hash
                    """,
                    (
                        row.id,
                        row.email,
                        row.role,
                        row.full_name,
                        row.is_active,
                        row.organization_id,
                        row.created_at,
                        row.updated_at,
                        row.password_hash,
                    ),
                )
                if exists:
                    stats.updated += 1
                else:
                    stats.inserted += 1
        conn.commit()
    return stats


def write_report(mode: str, total_rows: int, valid_rows: int, stats: ImportStats, rejected: list[dict[str, Any]]) -> None:
    report = {
        "source": str(INPUT_PATH.relative_to(ROOT)),
        "mode": mode,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "total_rows": total_rows,
        "valid_rows": valid_rows,
        "inserted": stats.inserted,
        "updated": stats.updated,
        "rejected": stats.rejected + len(rejected),
        "input_rejections": rejected,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.dry_run == args.apply:
        raise SystemExit("Use exactly one mode: --dry-run or --apply")

    rows = load_rows()
    valid_rows, rejected = validate_rows(rows)
    stats = ImportStats(rejected=len(rejected))

    if args.apply:
        if not args.database_url:
            raise SystemExit("Missing database URL. Provide --database-url or SUPABASE_DB_URL.")
        applied_stats = apply_upsert(args.database_url, valid_rows)
        stats.inserted = applied_stats.inserted
        stats.updated = applied_stats.updated
        stats.rejected += applied_stats.rejected

    write_report("apply" if args.apply else "dry-run", len(rows), len(valid_rows), stats, rejected)

    print("Import summary")
    print(f"- total: {len(rows)}")
    print(f"- valid: {len(valid_rows)}")
    print(f"- inserted: {stats.inserted}")
    print(f"- updated: {stats.updated}")
    print(f"- rejected: {stats.rejected}")
    print(f"- report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
