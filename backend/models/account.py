from pydantic import BaseModel, ConfigDict
from typing import Optional
import uuid

class EngineConfigModel(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        frozen=True,
        # strict=True
    )

    id:      uuid.UUID
    version: str
    depth:   Optional[int]