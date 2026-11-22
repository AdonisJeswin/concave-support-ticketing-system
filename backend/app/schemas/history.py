from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class HistoryOut(BaseModel):
    id: int
    ticket_id: int
    actor_id: Optional[int] = None
    actor_name: Optional[str] = None
    action: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
