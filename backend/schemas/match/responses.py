from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class MatchMoveResponseModel(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        frozen=True,
        strict=True,
    )

    fen: str
    status: str
    result: Optional[str] = None
    uci: Optional[str] = None
    san: Optional[str] = None
    server_now: datetime
    turn_started_at: datetime
    white_time_remaining_ms: int
    black_time_remaining_ms: int


class MatchFetchResponseModel(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        frozen=True,
        strict=True,
    )