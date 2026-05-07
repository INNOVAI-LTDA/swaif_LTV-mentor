from __future__ import annotations

from pathlib import Path

from app.storage.contact_user_repository import ContactUserRepository


def test_contact_user_repository_v2_read_write_cycle(tmp_path: Path) -> None:
    store_file = tmp_path / "contacts_users_v2.json"
    repo = ContactUserRepository(store_file)

    created = repo.create(
        id="ct_1",
        full_name="Contato Um",
        email="Contato@Example.com",
        role="provider",
        is_active=True,
    )

    assert created["email"] == "contato@example.com"
    assert store_file.exists()

    reloaded = ContactUserRepository(store_file)
    items = reloaded.list_items()
    assert len(items) == 1
    assert items[0]["id"] == "ct_1"
    assert items[0]["role"] == "provider"

    updated = reloaded.update("ct_1", full_name="Contato Ajustado")
    assert updated["full_name"] == "Contato Ajustado"
    assert reloaded.get_by_id("ct_1")["full_name"] == "Contato Ajustado"
