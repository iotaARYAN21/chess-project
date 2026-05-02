from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
import uuid

class MoveEntry(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        frozen=True,
        strict=True,
    )
    uci: str
    san: str


class MatchFetchResponse(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        frozen=True,
        strict=True,
    )

    match_id:                 uuid.UUID
    white_elo_initial:        int
    black_elo_initial:        int
    started_at:               datetime

    status:                   str
    result:                   Optional[str]
    ended_at:                 Optional[datetime]

    fen:                      str
    white_time_remaining_ms:  int
    black_time_remaining_ms:  int
    turn_started_at:          datetime
    move_number:              int
    moves:                    List[MoveEntry]

class MatchMoveResponse(BaseModel):
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
