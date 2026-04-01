# FastAPI route for admin_protocols
from fastapi import APIRouter, HTTPException
from backend.app.services.protocols_service import get_all_protocols

router = APIRouter()

@router.get("/admin/protocols")
def list_protocols():
    try:
        return get_all_protocols()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
