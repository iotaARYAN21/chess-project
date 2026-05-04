from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid
from http import HTTPStatus
from db.queries import get_all_engines, get_all_game_modes, get_time_controls_by_mode


router = APIRouter(prefix='/api', tags=["Lobby"])


class EngineResponse(BaseModel):
    id: uuid.UUID
    username: str
    is_active: bool
    version: str
    depth: Optional[int] = None

class GameModeResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    time_string: str


@router.get("/engines", response_model=List[EngineResponse])
async def fetch_engines():
    """
    Fetches all available engine accounts to populate the bot selector.
    """
    try:
        # Calls the function that joins engine_account and account tables
        rows = await get_all_engines()
        
        # Convert asyncpg.Record objects to standard Python dictionaries
        return [dict(r) for r in rows]
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, 
            detail=f"Failed to fetch engines: {e}"
        )

@router.get("/game-modes", response_model=List[GameModeResponse])
async def fetch_game_modes():
    try:
        # Fetch the base game modes (id, name, description)
        modes_records = await get_all_game_modes()
        
        result = []
        for mode in modes_records:
            # Fetch associated time controls for this specific game mode
            tcs = await get_time_controls_by_mode(mode["name"])
            
            time_string = "N/A"
            # If time controls exist, format the first one for the UI card
            if tcs:
                first_tc = tcs[0]
                # Assuming base_time is in seconds, convert to minutes for the display
                base_mins = first_tc["base_time"] // 60
                incr_secs = first_tc["incr_time"]
                time_string = f"{base_mins} + {incr_secs}"

            result.append({
                "id": mode["id"],
                "name": mode["name"],
                "description": mode["description"],
                "time_string": time_string
            })
            
        return result
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, 
            detail=f"Failed to fetch game modes: {e}"
        )