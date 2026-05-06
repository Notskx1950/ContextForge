from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EvalRunCreate(BaseModel):
    name: str
    dataset_name: str


class EvalRunRead(BaseModel):
    id: int
    name: str
    dataset_name: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}
