from re import sub

import jwt
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    OAuth2PasswordBearer,
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from dotenv import load_dotenv, find_dotenv
from typing import Tuple
from enum import Enum

from sqlalchemy import UUID
from db.queries import get_account_by_username, get_admin_by_id, get_player_by_email, get_admin_by_email, get_ban_user_if_present, get_account_by_id, get_player_by_id, lift_ban_admin, lift_ban_user

load_dotenv(find_dotenv())

def safe_load_env_var(env_key: str) -> str:
    env_val = os.getenv(env_key)
    if not env_val:
        raise RuntimeError(f"{env_key} env var is not set")
    return env_val

class AdminLevel(str, Enum):
    MODERATOR = 1
    ADMIN = 2
    SUPERADMIN = 3

JWT_SECRET_KEY = safe_load_env_var("JWT_SECRET_KEY")
JWT_ALGORITHM = safe_load_env_var("JWT_ALGORITHM")


def create_access_token(data: dict):
    to_encode = data.copy()
    token = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def decode_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")


# oauth2_scheme = OAuth2PasswordBearer(
#     # NOTE: both the fields are just for metadata
#     tokenUrl="/auth/login",
#     description="looks for Authorization header, parses its value: `Bearer <token>` and \
#         extracts the `token` and sends it"
# )

get_cred = HTTPBearer()
class AdminChecker:
    def __init__(self, admin_level_req: AdminLevel):
        # Store the required level when the dependency is declared
        self.admin_level_req = admin_level_req

    async def __call__(
        self, 
        credentials: HTTPAuthorizationCredentials = Depends(get_cred)
    ):
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
                options={"require": ["sub","username","role","admin_level"]},  # strictly enforce presence of these keys
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
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        id = payload.get("sub")
        sub = payload.get("username")
        role = payload.get("role")
        admin_level = payload.get("admin_level")
        
        if (not id) or (not isinstance(id, str)):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: missing `sub` field",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not admin_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required",
            )

        if admin_level == "moderator":
            admin_level_value = AdminLevel.MODERATOR.value
        elif admin_level == "admin":
            admin_level_value = AdminLevel.ADMIN.value
        elif admin_level == "superadmin":
            admin_level_value = AdminLevel.SUPERADMIN.value
        else:     
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required",
            )

        if not role or role != "sysadmin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required",
            )
            
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: missing `sub` field",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not isinstance(sub, str):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        if admin_level_value < self.admin_level_req.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Higher level privileges required",
            )
            
        # try:
        #     uuid_id = UUID(id)
        # except ValueError:
        #     raise HTTPException(
        #         status_code=status.HTTP_401_UNAUTHORIZED,
        #         detail="Invalid token payload: `sub` value is not a valid UUID",
        #         headers={"WWW-Authenticate": "Bearer"},
        #     )
            
        # Check if user is banned 
        acc = await get_admin_by_id(id)

        if not acc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        if acc["is_banned"]:
            ban = await get_ban_user_if_present(acc["id"])
            
            if ban:
                raise HTTPException(status_code=403,detail="Account is banned until {}".format(ban["expires_at"] if ban["expires_at"] else "the end of time!"))

            await lift_ban_admin(acc["id"])        
                
        return payload

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(get_cred),
) -> str:
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
            options={"require": ["sub"]},  # strictly enforce presence of these keys
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    sub = payload.get("username")

    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing `sub` field",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not isinstance(sub, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    id = payload.get("sub")
    
    if not id or not isinstance(id, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing `sub` field",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # try:
    #     uuid_id = UUID(id)
    # except ValueError:
    #         raise HTTPException(
    #             status_code=status.HTTP_401_UNAUTHORIZED,
    #             detail="Invalid token payload: `sub` value is not a valid UUID",
    #             headers={"WWW-Authenticate": "Bearer"},
    #         )
            
    # Check if user is banned 
    acc = await get_player_by_id(id)
    
    if not acc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if acc["is_banned"]:
        ban = await get_ban_user_if_present(acc["id"])
        
        if ban:
            raise HTTPException(status_code=403,detail="Account is banned until {}".format(ban["expires_at"] if ban["expires_at"] else "the end of time!"))

        await lift_ban_user(acc["id"])

    return sub


def get_user_id(credentials: HTTPAuthorizationCredentials = Depends(get_cred)) -> str:
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
            options={"require": ["sub"]},  # strictly enforce presence of these keys
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

    return sub


def calculate_elos(
    white_rating: int, black_rating: int, result: str, k_factor: int = 32
) -> Tuple[int, int]:
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
