from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class TraceLabel(str, Enum):
    reasoning = "reasoning"
    asking = "asking"
    proposing = "proposing"
    confirmed = "confirmed"
    executed = "executed"


class ActionKind(str, Enum):
    read_only = "read_only"
    reversible = "reversible"
    consequential = "consequential"
    harmful = "harmful"


class ActionStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    executing = "executing"
    executed = "executed"
    failed = "failed"
    cancelled = "cancelled"


class Action(BaseModel):
    action_id: str
    kind: ActionKind
    tool: str
    payload: dict[str, Any]
    status: ActionStatus = ActionStatus.pending
    situation_version: int | None = None
    approved_at: datetime | None = None
    payload_hash: str
    result: dict[str, Any] | None = None


class TraceEvent(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    label: TraceLabel
    message: str
    data: dict[str, Any] = Field(default_factory=dict)


class RunRequest(BaseModel):
    text: str
    locale: str = "en-IN"
    client_time: datetime | None = None
    chaos: str | None = None




class ConfirmRequest(BaseModel):
    expected_situation_version: int


class ExecuteRequest(BaseModel):
    expected_situation_version: int
