# FastAPI route for admin_users
from fastapi import APIRouter, HTTPException
from app.services.users_service import get_all_users, create_user

router = APIRouter()

@router.get("/admin/users")
def list_users():
    try:
        return get_all_users()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/users")
def create_user_api(payload: dict):
    try:
        return create_user(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
