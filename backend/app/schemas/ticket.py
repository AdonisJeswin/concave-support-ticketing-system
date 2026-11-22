from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum
from pydantic import BaseModel, Field
from backend.app.schemas.reply import ReplyOut
from backend.app.schemas.history import HistoryOut

class TicketPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class TicketStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"
    ESCALATED = "ESCALATED"

class TicketCreate(BaseModel):
    category_id: int
    subject: str = Field(..., min_length=5, max_length=150)
    description: str = Field(..., min_length=10, max_length=5000)

class TicketPriorityUpdate(BaseModel):
    priority: TicketPriority
    reason: str = Field(..., min_length=5, max_length=1000)

class TicketAssignUpdate(BaseModel):
    assigned_agent_id: Optional[int] = None

class TicketResolve(BaseModel):
    resolution_note: Optional[str] = Field(None, max_length=2000)

class TicketReopen(BaseModel):
    reason: str = Field(..., min_length=10, max_length=2000)

class TicketEscalationResolve(BaseModel):
    new_agent_id: int
    directive_reason: str = Field(..., min_length=5, max_length=2000)

class TicketOut(BaseModel):
    id: int
    ticket_number: str
    member_id: int
    member_name: Optional[str] = None
    member_email: Optional[str] = None
    category_id: int
    category_name: Optional[str] = None
    assigned_agent_id: Optional[int] = None
    assigned_agent_name: Optional[str] = None
    subject: str
    description: str
    priority: str
    status: str
    created_at: datetime
    due_at: datetime
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    reopen_count: int
    tat_paused_at: Optional[datetime] = None
    total_paused_seconds: int
    is_overdue: bool = False
    is_paused: bool = False
    remaining_sla_seconds: Optional[int] = None

    class Config:
        from_attributes = True

class TicketDetailOut(TicketOut):
    replies: List[ReplyOut] = []
    history: List[HistoryOut] = []
