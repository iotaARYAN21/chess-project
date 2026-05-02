import uuid
from pydantic import BaseModel, ConfigDict

class BotMatchRequest(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        frozen=True,
        strict=True,
    )

    time_control_id: uuid.UUID
    bot_username: str
