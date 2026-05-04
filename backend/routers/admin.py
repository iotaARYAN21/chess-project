from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, field_validator
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from db.queries import (
    ban_user,
    get_active_bans,
    get_all_bans,
    is_banned,
    lift_ban,
    log_suspicious_activity,
    get_unresolved_cheat_logs,
    resolve_cheat_log,
    get_all_cheat_logs,
    resolve_anti_cheat_log_with_ban,
)
from utils import AdminLevel, AdminChecker
from enum import Enum

router = APIRouter(prefix="/admin", tags=["admin"])


class BanType(str, Enum):
    NONE = "none"
    TEMP_24H = "24h"
    TEMP_7D = "7d"
    PERMANENT = "permanent"


class ResolveRequest(BaseModel):
    log_id: uuid.UUID
    account_id: uuid.UUID
    ban_type: BanType = BanType.NONE
    reason: Optional[str] = "Cheating detected via anti-cheat logs"


class ResolveResponse(BaseModel):
    success: bool
    log_id: uuid.UUID
    account_id: uuid.UUID
    banned: bool
    ban_type: Optional[str]
    expires_at: Optional[datetime]
    resolved_at: datetime


_BAN_DURATIONS: dict[BanType, Optional[timedelta]] = {
    BanType.NONE: None,
    BanType.TEMP_24H: timedelta(hours=24),
    BanType.TEMP_7D: timedelta(days=7),
    BanType.PERMANENT: None,
}


def _compute_expires_at(ban_type: BanType) -> Optional[datetime]:
    """Return the expiry timestamp for temporary bans, else None."""
    delta = _BAN_DURATIONS.get(ban_type)
    if delta is None:
        return None
    return datetime.now(tz=timezone.utc) + delta


def _db_ban_type(ban_type: BanType) -> str:
    """Map BanType enum to the DB column value expected by the CHECK constraint."""
    if ban_type == BanType.NONE:
        return "none"
    if ban_type == BanType.PERMANENT:
        return "permanent"
    return "temporary"


@router.get("/unresolved-cheat-logs")
async def get_unresolved_cheat_logs_endpoint(
    payload=Depends(AdminChecker(AdminLevel.MODERATOR)),
):
    """Fetches all unresolved suspicious activity logs for the dashboard."""
    try:
        logs = await get_unresolved_cheat_logs()

        return [dict(log) for log in logs]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/cheat-logs")
async def get_all_cheat_logs_endpoint(
    payload=Depends(AdminChecker(AdminLevel.MODERATOR)),
):
    """Fetches all unresolved suspicious activity logs for the dashboard."""
    try:
        logs = await get_all_cheat_logs()

        return [dict(log) for log in logs]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/anticheat-resolve",
)
async def resolve_anticheat_endpoint(
    payload: ResolveRequest, admincred=Depends(AdminChecker(AdminLevel.MODERATOR))
) -> ResolveResponse:
    expires_at = _compute_expires_at(payload.ban_type)
    db_ban_type = _db_ban_type(payload.ban_type)
    is_banned = payload.ban_type != BanType.NONE
    resolved_at = datetime.now(tz=timezone.utc)

    try:
        await resolve_anti_cheat_log_with_ban(
            log_id=payload.log_id,
            user_id=payload.account_id,
            admin_id=admincred["sub"],
            ban_type=db_ban_type,
            reason=payload.reason,
            expires_at=expires_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

    return ResolveResponse(
        success=True,
        log_id=payload.log_id,
        account_id=payload.account_id,
        banned=is_banned,
        ban_type=db_ban_type if is_banned else None,
        expires_at=expires_at,
        resolved_at=resolved_at,
    )


@router.post("/resolve-log")
async def handle_resolve_log(
    payload: ResolveRequest, admincred=Depends(AdminChecker(AdminLevel.MODERATOR))
):
    admin_id = admincred["sub"]  # Extract admin ID from token payload

    await resolve_cheat_log(payload.log_id, admin_id)

    # 2. If a ban type was specified in the modal, apply it
    if payload.ban_type != "none":
        await ban_user(
            account_id=payload.account_id,
            admin_id=admin_id,
            ban_type=payload.ban_type,
            reason=payload.reason,
        )

    return {"status": "success", "message": "Log resolved and action applied"}


@router.get("/bans")
async def check_all_user_bans(admincred=Depends(AdminChecker(AdminLevel.MODERATOR))):
    """Returns all active bans"""
    try:
        active_bans = await get_all_bans()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    return [dict(ban) for ban in active_bans]

@router.put("/unban/{ban_id}")
async def unban_user(
    ban_id: uuid.UUID, admincred=Depends(AdminChecker(AdminLevel.MODERATOR))
):
    """Lift a ban for a specific user."""
    try:
        await lift_ban(ban_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    return {"status": "success", "message": "Ban lifted successfully"}

@router.get("/bans/{account_id}")
async def check_user_bans(
    account_id: uuid.UUID, admincred=Depends(AdminChecker(AdminLevel.MODERATOR))
):
    """Returns all active bans for a specific user."""
    try:
        active_bans = await get_active_bans(account_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    return [dict(ban) for ban in active_bans]


@router.get("/is-banned/{account_id}")
async def check_if_banned(
    account_id: uuid.UUID, admincred=Depends(AdminChecker(AdminLevel.MODERATOR))
):
    """Quick boolean check if a user is currently restricted."""
    banned = await is_banned(account_id)
    return {"account_id": account_id, "is_banned": banned}


@router.post("/log-activity")
async def report_suspicious_activity(
    user_id: uuid.UUID,
    match_id: uuid.UUID,
    sus_score: float,
    admincred=Depends(AdminChecker(AdminLevel.MODERATOR)),
):
    """Internal endpoint to log suspicious activity from the game server."""
    log_id = await log_suspicious_activity(user_id, match_id, sus_score)
    return {"log_id": log_id}