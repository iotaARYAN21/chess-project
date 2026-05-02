import jwt
import os
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv, find_dotenv
from typing import Tuple

load_dotenv(find_dotenv())

def safe_load_env_var(env_key: str) -> str:
    env_val = os.getenv(env_key)
    if not env_val:
        raise RuntimeError(f"{env_key} env var is not set")
    return env_val


JWT_SECRET_KEY  = safe_load_env_var("JWT_SECRET_KEY")
JWT_ALGORITHM   = safe_load_env_var("JWT_ALGORITHM")


# oauth2_scheme = OAuth2PasswordBearer(
#     # NOTE: both the fields are just for metadata
#     tokenUrl="/auth/login",
#     description="looks for Authorization header, parses its value: `Bearer <token>` and \
#         extracts the `token` and sends it"
# )

get_cred = HTTPBearer()


def get_user_id(credentials: HTTPAuthorizationCredentials = Depends(get_cred)) -> uuid.UUID:
    """
        oauth2_scheme injects the token
        
        get_identity assumes the following:
            token type is jwt, 
            secret is JWT_SECRET_KEY env var
            algorithm is JWT_ALGORITHM env var
            payload (decoded token) must have `sub`, `type` and `exp` fields

        decodes token using JWT_SECRET_KEY & JWT_ALGORITHM to get payload,
        extracts `sub` & `type` from the payload and 
        checks if present or absent
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(
            jwt=token,
            key=JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub"]}, # strictly enforce presence of these keys
            leeway=5,  # handles minor clock drift of 5 seconds
        )

    # NOTE: acc to RFC 7519 (JWT standard)
    # reserved words 
    #       exp -> expiration time
    #       sub -> subject
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    sub = payload.get("sub")

    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing `sub` field",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not isinstance(sub, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: `sub` value is not string",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return uuid.UUID(sub)

def get_user_id_from_token(token: str) -> uuid.UUID:
    """Same logic as get_user_id but takes a raw token string — for WebSocket use."""
    try:
        payload = jwt.decode(
            jwt=token,
            key=JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub"]},
            leeway=5,
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    sub = payload.get("sub")
    if not sub or not isinstance(sub, str):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token payload")

    return uuid.UUID(sub)


def calculate_elos(white_rating: int, black_rating: int, result: str, k_factor:int=32) -> Tuple[int, int]:
    """
        Compute updated Elo ratings using the standard formula:  
            * Expected score: E = 1 / (1 + 10^((R_opp - R) / 400))  
            * New rating: R' = R + K * (S - E)  

        Given white and black Elo ratings and the game result ("white", "black", "draw"),
        returns updated integer ratings for both players.

        Only use this when game has terminated and result is not None
    """
    
    if result == "draw":
        white_outcome = black_outcome = 0.5
    elif result == "white":
        white_outcome, black_outcome = 1.0, 0.0
    elif result == "black":
        white_outcome, black_outcome = 0.0, 1.0
    else:
        raise ValueError("Invalid result")

    white_expected = 1 / (1 + 10 ** ((black_rating - white_rating) / 400))
    black_expected = 1 - white_expected

    new_white = white_rating + k_factor * (white_outcome - white_expected)
    new_black = black_rating + k_factor * (black_outcome - black_expected)

    return round(new_white), round(new_black)


import json
from fastapi import WebSocket
from typing import defaultdict

class ConnectionManager:
    def __init__(self):
        self.rooms: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, match_id: str):
        await websocket.accept()
        self.rooms[match_id].append(websocket)

    def disconnect(self, websocket: WebSocket, match_id: str):
        self.rooms[match_id].remove(websocket)
        if not self.rooms[match_id]:
            del self.rooms[match_id]

    async def broadcast_to_match(self, match_id: str, payload: dict):
        for ws in self.rooms.get(match_id, []):
            try:
                await ws.send_text(json.dumps(payload, default=str))
            except Exception:
                pass