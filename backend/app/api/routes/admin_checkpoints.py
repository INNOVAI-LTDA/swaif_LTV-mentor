# FastAPI route for admin_checkpoints
from fastapi import APIRouter, HTTPException
from backend.app.services.checkpoints_service import get_all_checkpoints

router = APIRouter()

@router.get("/admin/checkpoints")
def list_checkpoints():
    try:
        return get_all_checkpoints()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
