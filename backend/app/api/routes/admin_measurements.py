# FastAPI route for admin_measurements
from fastapi import APIRouter, HTTPException
from backend.app.services.measurements_service import get_all_measurements

router = APIRouter()

@router.get("/admin/measurements")
def list_measurements():
    try:
        return get_all_measurements()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
