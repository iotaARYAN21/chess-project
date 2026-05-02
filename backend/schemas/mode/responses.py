from pydantic import BaseModel, ConfigDict
from typing import List
import uuid
from models.game import TimeControlModel


class GameModeDetailResponse(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        frozen=True,
        strict=True,
    )

    id: uuid.UUID
    name: str
    description: str
    time_controls: List[TimeControlModel]


class GameModeDetailListResponse(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        frozen=True,
        strict=True,
    )

    game_modes: List[GameModeDetailResponse]