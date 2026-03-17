from app.storage.protocol_repository import ProtocolRepository


def test_protocol_repository_lists_by_organization(tmp_path) -> None:
    repo = ProtocolRepository(tmp_path / "protocols.json")
    repo.create(organization_id="org_1", name="Metodo Produto A", code="org-1-metodo")
    repo.create(organization_id="org_2", name="Metodo Produto B", code="org-2-metodo")

    items = repo.list_by_organization("org_1")

    assert len(items) == 1
    assert items[0]["organization_id"] == "org_1"
