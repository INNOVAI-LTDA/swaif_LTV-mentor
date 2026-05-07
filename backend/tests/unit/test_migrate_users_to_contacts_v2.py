from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[2]))

from data_ops.migrate_users_to_contacts_v2 import collect_candidates, deduplicate_candidates


def test_role_mapping_from_sources() -> None:
    candidates = collect_candidates(
        users=[{"id": "u1", "email": "a@x.com", "role": "admin"}, {"id": "u2", "email": "b@x.com", "role": "mentor"}],
        mentors=[{"id": "m1", "full_name": "Mentor", "email": "m@x.com"}],
        students=[{"id": "s1", "full_name": "Aluno", "email": "s@x.com"}],
    )
    by_id = {item.id: item.role for item in candidates}
    assert by_id["u1"] == "admin"
    assert by_id["u2"] == "provider"
    assert by_id["m1"] == "provider"
    assert by_id["s1"] == "client"


def test_deduplication_uses_precedence_admin_provider_client() -> None:
    candidates = collect_candidates(
        users=[{"id": "u1", "email": "same@x.com", "role": "mentor"}, {"id": "u2", "email": "same@x.com", "role": "admin"}],
        mentors=[],
        students=[{"id": "s1", "full_name": "Aluno", "email": "same@x.com"}],
    )
    deduped, duplicates = deduplicate_candidates(candidates)
    assert len(deduped) == 1
    assert deduped[0].id == "u2"
    assert deduped[0].role == "admin"
    assert len(duplicates) == 2


def test_required_fields_are_enforced() -> None:
    with pytest.raises(ValueError, match="Missing required field 'email'"):
        collect_candidates(users=[{"id": "u1", "role": "admin"}], mentors=[], students=[])

    with pytest.raises(ValueError, match="Missing required field 'full_name'"):
        collect_candidates(users=[], mentors=[], students=[{"id": "s1", "email": "s@x.com"}])


def test_final_role_counts_after_dedupe() -> None:
    candidates = collect_candidates(
        users=[
            {"id": "u1", "email": "admin@x.com", "role": "admin"},
            {"id": "u2", "email": "mentor@x.com", "role": "mentor"},
        ],
        mentors=[{"id": "m1", "full_name": "Mentor", "email": "mentor@x.com"}],
        students=[{"id": "s1", "full_name": "Aluno", "email": "student@x.com"}],
    )
    deduped, _ = deduplicate_candidates(candidates)
    counts = {"admin": 0, "provider": 0, "client": 0}
    for item in deduped:
        counts[item.role] += 1
    assert counts == {"admin": 1, "provider": 1, "client": 1}
