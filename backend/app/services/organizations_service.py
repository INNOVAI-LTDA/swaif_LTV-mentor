from app.storage.organization_repository import OrganizationRepository

def get_all_organizations():
    repo = OrganizationRepository()
    return repo.list_organizations()


def create_organization(payload: dict):
    required_fields = ["name", "brand_name", "slug", "timezone", "currency", "status"]
    missing = [f for f in required_fields if not payload.get(f)]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
    try:
        repo = OrganizationRepository()
        return repo.create(
            name=payload.get("name"),
            slug=payload.get("slug"),
            client_id=payload.get("client_id"),
            code=payload.get("code"),
            description=payload.get("description"),
            delivery_model=payload.get("delivery_model"),
            brand_name=payload.get("brand_name"),
            cnpj=payload.get("cnpj"),
            timezone=payload.get("timezone"),
            currency=payload.get("currency"),
            status=payload.get("status"),
        )
    except Exception as e:
        import logging
        logging.exception("Erro ao criar organização")
        raise
