from pydantic import BaseModel, ConfigDict
from uuid import UUID


class TimeControlModel(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        frozen=True,
        strict=True,
    )

    id: UUID
    game_mode_id: UUID
    base_time: int
    incr_time: int