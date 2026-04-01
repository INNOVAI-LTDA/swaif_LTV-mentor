# FastAPI route for admin_users
from fastapi import APIRouter, HTTPException
from backend.app.services.users_service import get_all_users

router = APIRouter()

@router.get("/admin/users")
def list_users():
    try:
        return get_all_users()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
