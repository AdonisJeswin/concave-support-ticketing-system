from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class ReplyCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    is_waiting_for_member: bool = False  # Agent can toggle to pause TAT

class ReplyOut(BaseModel):
    id: int
    ticket_id: int
    sender_id: int
    sender_name: Optional[str] = None
    sender_role: Optional[str] = None
    message: str
    created_at: datetime

    class Config:
        from_attributes = True
