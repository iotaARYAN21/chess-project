from pydantic import BaseModel, ConfigDict

class MatchMoveRequestModel(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        frozen=True,
        strict=True,
    )

    uci: str