# routers/modes.py

from fastapi import APIRouter, HTTPException
from http import HTTPStatus
from pydantic import ValidationError

from db.queries import get_all_game_modes, get_time_controls_by_game_mode_id
from schemas.mode.responses import GameModeDetailResponse, GameModeDetailListResponse
from models.game import GameModeModel, TimeControlModel

router = APIRouter(
    prefix='/modes', 
    tags=["modes"]
)


@router.get(
    "/", 
    response_model=GameModeDetailListResponse
)
async def get_game_modes():
    """ 
        we are getting all the game modes with their basic information and 
        the corresponding time_controls as a list 
    """
    # get `game_mode` records and check for their existence
    mode_records = await get_all_game_modes()
    if not mode_records:
        raise HTTPException(HTTPStatus.NOT_FOUND, "`game_mode` records not found")

    game_modes: list[GameModeDetailResponse] = []
    for record in mode_records:
        # validate every mode in mode_records against GameModeModel
        try:
            mode = GameModeModel.model_validate(dict(record))
        except ValidationError as e:
            raise HTTPException(HTTPStatus.INTERNAL_SERVER_ERROR, f"Data integrity error in `game_mode` record: {e}")

        # for a given game_mode_id get the `time_control` records and validate against TimeControlModel
        tc_records = await get_time_controls_by_game_mode_id(mode.id)
        try:
            time_controls = [
                TimeControlModel.model_validate(dict(tc)) for tc in tc_records
            ]
        except ValidationError as e:
            raise HTTPException(HTTPStatus.INTERNAL_SERVER_ERROR, f"Data integrity error in `time_control` records for mode `{mode.id}`: {e}")

        game_modes.append(
            GameModeDetailResponse(
                **mode.model_dump(),
                time_controls=time_controls,
            )
        )

    return GameModeDetailListResponse(game_modes=game_modes)