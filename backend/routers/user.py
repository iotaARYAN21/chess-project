from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional
from utils import get_current_user

from db.queries import (
    get_user_profile,
    update_user_profile,
    get_matches_by_game_mode,
     get_user_stats_by_name,
     get_all_user_matches,
     get_match_by_id
)

router = APIRouter(prefix="/users", tags=["users"])


class ProfileUpdate(BaseModel):
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


# def get_current_user():
#     return "shreesh"  # TODO replace with auth


# PROFILE

@router.get("/{username}")
async def get_user_profile_route(username: str):
    user = await get_user_profile(username)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return dict(user)


@router.put("/{username}/profile")
async def update_profile(username: str, data: ProfileUpdate):
    # current_user = get_current_user()

    # if current_user != username:
    #     raise HTTPException(status_code=403, detail="Not authorized")

    try:
        await update_user_profile(
            username,
            bio=data.bio,
            avatar_url=data.avatar_url
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "Profile updated"}


# STATS 

@router.get("/{username}/stats")
async def get_user_stats(username: str):
    rows = await get_user_stats_by_name(username)

    return [
        {
            "game_mode": r["game_mode"],
            "elo": r["elo"],
            "wins": r["n_wins"],
            "losses": r["n_losses"],
            "draws": r["n_draws"],
        }
        for r in rows
    ]


# MATCHES

@router.get("/{username}/matches")
async def get_user_matches(
    username: str,
    game_mode: Optional[str] = Query(None)
):
    if not game_mode:
        # raise HTTPException(status_code=400, detail="game_mode required")
        rows = await get_all_user_matches(username)
    else:
        rows = await get_matches_by_game_mode(username, game_mode)

    return [dict(r) for r in rows]


@router.get("/match/{match_id}/pgn")
async def get_match_pgn(match_id:str):
    """Fetch only the PGN for a specific match."""
    import uuid
    match = await get_match_by_id(uuid.UUID(match_id)) # Uses existing query
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return {"pgn": match["final_pgn"]}