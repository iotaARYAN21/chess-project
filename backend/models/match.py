from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Literal, Optional, List

class MatchModel(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        frozen=True,
        strict=True,
    )

    id: UUID
    white_id: Optional[UUID] = None
    black_id: Optional[UUID] = None
    time_control_id: UUID
  
    white_elo_initial: int
    black_elo_initial: int
    started_at: datetime
   
    status: Literal["active", "completed"] = "active"
    result: Optional[Literal["white", "black", "draw"]] = None
    ended_at: Optional[datetime] = None
    white_elo_shift: Optional[int] = None
    black_elo_shift: Optional[int] = None
    final_fen: Optional[str] = None
    final_pgn: Optional[str] = None

class MatchStateModel(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        frozen=True,
        strict=True,
    )

    match_id: UUID
    fen: str
    white_time_remaining_ms: int
    black_time_remaining_ms: int
    turn_started_at: datetime
    move_number: int
    move_history: List[str]
