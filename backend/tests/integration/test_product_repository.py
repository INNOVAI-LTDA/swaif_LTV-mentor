from app.storage.organization_repository import OrganizationRepository


def test_product_repository_creates_and_lists_products_by_client(tmp_path) -> None:
    repo = OrganizationRepository(tmp_path / "organizations.json")

    created = repo.create(
        name="Acelerador Medico Premium",
        client_id="cli_1",
        code="AMP-PREMIUM",
        slug="acelerador-premium",
        description="Produto premium",
    )

    assert created["id"] == "org_1"
    assert created["client_id"] == "cli_1"
    assert repo.get_by_id("org_1")["name"] == "Acelerador Medico Premium"
    assert len(repo.list_by_client("cli_1")) == 1


def test_product_repository_rejects_duplicate_code_in_same_client(tmp_path) -> None:
    repo = OrganizationRepository(tmp_path / "organizations.json")
    repo.create(name="Acelerador Medico Premium", client_id="cli_1", code="AMP-PREMIUM")

    try:
        repo.create(name="Produto Novo", client_id="cli_1", code="AMP-PREMIUM")
    except ValueError as exc:
        assert str(exc) == "organization code already exists"
    else:
        raise AssertionError("ValueError was expected")
