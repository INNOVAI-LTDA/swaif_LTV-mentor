# FastAPI route for admin_enrollments
from fastapi import APIRouter, HTTPException
from backend.app.services.enrollments_service import get_all_enrollments

router = APIRouter()

@router.get("/admin/enrollments")
def list_enrollments():
    try:
        return get_all_enrollments()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
