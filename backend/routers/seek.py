from fastapi import APIRouter, HTTPException, Depends
from http import HTTPStatus
from pydantic import ValidationError
from datetime import datetime, timezone
import uuid
from utils import get_user_id
from db.queries import get_account_by_username, get_time_control_by_id, \
    get_user_stats_by_game_mode_id, create_match, get_account_by_id
from schemas.seek.requests import BotMatchRequest
from models.game import TimeControlModel

router = APIRouter(prefix='/api')

# def get_user_id():
#     return uuid.UUID("a1000000-0000-0000-0000-000000000001")

@router.post('/seek')
async def create_bot_match(
    request: BotMatchRequest, 
    user_id: uuid.UUID = Depends(get_user_id)
):
    seek_at = datetime.now(timezone.utc)

    user_account_record = await get_account_by_id(user_id)
    if not user_account_record:
        raise HTTPException(HTTPStatus.INTERNAL_SERVER_ERROR, f"user `account` record not found - (Inconsistent state)")

    # fetch time_control record and check its existence
    time_control_record = await get_time_control_by_id(request.time_control_id)
    if not time_control_record: 
        raise HTTPException(HTTPStatus.FORBIDDEN, f"`time_control` record not found - Illegal creation request")
    
    # validate time_control record against TimeControlModel (db model)
    try:
        time_control : TimeControlModel = TimeControlModel.model_validate(dict(time_control_record))
    except ValidationError as e:
        raise HTTPException(HTTPStatus.INTERNAL_SERVER_ERROR,f"Data integrity error: `time_control` record corrupted {e}")

    # fetch bot account record and check its existence
    bot_account_record = await get_account_by_username(request.bot_username)
    if not bot_account_record:
        raise HTTPException(HTTPStatus.FORBIDDEN, "bot `account` record not found - Illegal creation request")
    
    # TODO: validation of bot account record is still left

    # fetch user stats and check
    # NOTE: whenever a user is created its stats shd be filled accordingly
    try:
        user_stat = await get_user_stats_by_game_mode_id(user_id, time_control.game_mode_id)
        user_elo = user_stat[0]["elo"]
    except Exception as e:
        raise HTTPException(HTTPStatus.INTERNAL_SERVER_ERROR, f"Failed to get stats of user for game_mode {time_control.game_mode_id}: {e}")
    
    try:
        new_game_id = await create_match(
            white_id=user_id,
            black_id=bot_account_record["id"],
            time_control_id=request.time_control_id,
            white_elo_initial=user_elo,
            black_elo_initial=user_elo + 10,
            started_at=seek_at,
        )
    except Exception as e:
        raise HTTPException(HTTPStatus.INTERNAL_SERVER_ERROR, f"Failed to create match: {e}")

    return {
        "status": "matched",
        "game_id": str(new_game_id),
        "opponent_name": bot_account_record["username"],
        "opponent_id": bot_account_record["id"],
    }