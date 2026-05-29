# FastAPI route for admin_organizations
from fastapi import APIRouter, HTTPException
from app.services.organizations_service import get_all_organizations, create_organization

router = APIRouter()

@router.get("/admin/organizations")
def list_organizations():
    try:
        return get_all_organizations()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/organizations")
def create_organization_api(payload: dict):
    try:
        return create_organization(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
