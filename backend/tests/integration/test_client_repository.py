from app.storage.client_repository import ClientRepository


def test_client_repository_creates_and_reads_client(tmp_path) -> None:
    repo = ClientRepository(tmp_path / "clients.json")

    created = repo.create(
        name="Clinica Horizonte",
        brand_name="Horizonte",
        cnpj="12345678000199",
        slug="clinica-horizonte",
    )

    assert created["id"] == "cli_1"
    assert repo.get_by_id("cli_1")["name"] == "Clinica Horizonte"
    assert len(repo.list_clients()) == 1


def test_client_repository_rejects_duplicate_cnpj(tmp_path) -> None:
    repo = ClientRepository(tmp_path / "clients.json")
    repo.create(name="Clinica Horizonte", cnpj="12345678000199")

    try:
        repo.create(name="Clinica Horizonte 2", cnpj="12345678000199")
    except ValueError as exc:
        assert str(exc) == "client cnpj already exists"
    else:
        raise AssertionError("ValueError was expected")
