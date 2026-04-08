from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/users", tags=["users"])

# MODELS 

class ProfileUpdate(BaseModel):
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


# Replace with actual DB calls later

fake_users = {
    "murali": {
        "bio": "Chess enthusiast",
        "avatar_url": "http://example.com/avatar.png",
        "followers": 10,
        "friends": 5
    }
}

# HELPERS

def get_current_user():
    # TODO: replace with real auth later
    return "murali"


# ENDPOINTS

@router.get("/{username}")
def get_user_profile(username: str):
    user = fake_users.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.put("/{username}/profile")
def update_profile(username: str, data: ProfileUpdate):
    current_user = get_current_user()

    if current_user != username:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = fake_users.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.bio is not None:
        user["bio"] = data.bio
    if data.avatar_url is not None:
        user["avatar_url"] = data.avatar_url

    return {"message": "Profile updated", "data": user}


@router.get("/{username}/stats")
def get_user_stats(username: str):
    # TODO: Replace with DB function call: GET_USER_STATS_BY_MODE
    return {
        "bullet": {"elo": 1200, "wins": 10, "losses": 5, "draws": 2},
        "blitz": {"elo": 1300, "wins": 20, "losses": 10, "draws": 3},
        "rapid": {"elo": 1400, "wins": 15, "losses": 8, "draws": 4},
        "classical": {"elo": 1500, "wins": 5, "losses": 2, "draws": 1},
    }


@router.get("/{username}/matches")
def get_user_matches(
    username: str,
    game_mode: Optional[str] = Query(None)
):
    # TODO: Replace with DB function call: GET_MATCHES_BY_GAME_MODE

    return {
        "username": username,
        "game_mode": game_mode,
        "matches": [
            {"id": 1, "opponent": "john", "result": "win"},
            {"id": 2, "opponent": "doe", "result": "loss"}
        ]
    }