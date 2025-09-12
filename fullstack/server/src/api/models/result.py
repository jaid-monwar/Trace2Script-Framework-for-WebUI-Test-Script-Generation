from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel


class ResultBase(SQLModel):
    result_gif: Optional[str] = Field(default=None)
    result_json_url: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Result(ResultBase, table=True):
    __tablename__ = "results"
    
    task_id: int = Field(primary_key=True, foreign_key="tasks.id")


class ResultRead(ResultBase):
    task_id: int
    result_gif: Optional[str]
    result_json_url: Optional[str]