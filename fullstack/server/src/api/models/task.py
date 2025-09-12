from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel


class TaskBase(SQLModel):
    task_name: str = Field(max_length=1000)
    status: str = Field(default="initial")
    llm_provider: str = Field(default="openai")
    llm_model: str = Field(default="gpt-4o")
    temperature: float = Field(default=0.6)
    context_length: int = Field(default=16000)
    base_url: Optional[str] = Field(default=None)
    api_key: Optional[str] = Field(default=None)
    browser_headless_mode: bool = Field(default=True)
    disable_security: bool = Field(default=True)
    window_width: int = Field(default=1280)
    window_height: int = Field(default=720)
    instruction: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    search_input_input: Optional[str] = Field(default=None)
    search_input_action: Optional[str] = Field(default=None)
    expected_outcome: Optional[str] = Field(default=None)
    expected_status: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    initiated_at: Optional[datetime] = Field(default=None)


class Task(TaskBase, table=True):
    __tablename__ = "tasks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")


class TaskCreate(SQLModel):
    task_name: str = Field(max_length=1000)


class TaskRead(TaskBase):
    id: int
    user_id: int


class TaskSummary(SQLModel):
    id: int
    task_name: str
    status: str


class AgentSettings(SQLModel):
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    temperature: Optional[float] = None
    context_length: Optional[int] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None


class BrowserSettings(SQLModel):
    browser_headless_mode: Optional[bool] = None
    disable_security: Optional[bool] = None
    window_width: Optional[int] = None
    window_height: Optional[int] = None


class TaskInitiate(SQLModel):
    instruction: str
    description: str
    search_input_input: str
    search_input_action: str
    expected_outcome: str
    expected_status: str
    api_key: str = None