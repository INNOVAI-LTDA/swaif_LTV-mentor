# FastAPI route for admin_organizations
from fastapi import APIRouter, HTTPException
from backend.app.services.organizations_service import get_all_organizations

router = APIRouter()

@router.get("/admin/organizations")
def list_organizations():
    try:
        return get_all_organizations()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
