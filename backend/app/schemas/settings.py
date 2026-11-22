from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field

class TATSettingOut(BaseModel):
    id: int
    priority: str
    tat_hours: int
    updated_by: int
    updated_at: datetime

    class Config:
        from_attributes = True

class TATSettingUpdate(BaseModel):
    tat_hours: int = Field(..., gt=0, le=168)  # Up to 1 week

class SystemSettingOut(BaseModel):
    id: int
    reopen_window_days: int
    max_reopen_attempts: int
    auto_close_days: Optional[int] = None
    updated_by: int
    updated_at: datetime

    class Config:
        from_attributes = True

class SystemSettingUpdate(BaseModel):
    reopen_window_days: Optional[int] = Field(None, gt=0, le=90)
    max_reopen_attempts: Optional[int] = Field(None, ge=0, le=10)
    auto_close_days: Optional[int] = Field(None, gt=0, le=90)

class DashboardMetrics(BaseModel):
    total_open_tickets: int
    overdue_tickets_count: int
    escalated_tickets_count: int
    resolved_today_count: int
    average_resolution_time_hours: float
    category_breakdown: Dict[str, int]
