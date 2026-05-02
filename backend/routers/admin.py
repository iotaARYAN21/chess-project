from fastapi import APIRouter,HTTPException
from pydantic import BaseModel
from db.queries import get_unresolved_cheat_logs

router = APIRouter(prefix="/admin",tags=["admin"])

@router.get("/cheat-logs")
async def get_cheat_logs():
    logs = await get_unresolved_cheat_logs()

    return [dict(log) for log in logs]

