from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.schemas.settings import (
    DashboardMetrics, TATSettingOut, TATSettingUpdate, SystemSettingOut, SystemSettingUpdate
)
from backend.app.dependencies import require_support_head
from backend.app.services import settings_service, sla_service

router = APIRouter(prefix="/api/admin", tags=["Admin & SLA Configuration"])

@router.get("/metrics", response_model=DashboardMetrics)
def get_metrics(
    current_user: User = Depends(require_support_head),
    db: Session = Depends(get_db)
):
    """Retrieve executive KPIs: Open, Overdue, Escalated, Resolved Today, ART, and Categories."""
    return settings_service.get_dashboard_metrics(db)

@router.get("/tat-settings", response_model=List[TATSettingOut])
def get_tat_settings(
    current_user: User = Depends(require_support_head),
    db: Session = Depends(get_db)
):
    """List turnaround time (TAT) hours configured per priority level."""
    settings_list = settings_service.get_all_tat_settings(db)
    return [TATSettingOut.model_validate(s) for s in settings_list]

@router.put("/tat-settings/{priority}", response_model=TATSettingOut)
def update_tat_setting(
    priority: str,
    data: TATSettingUpdate,
    current_user: User = Depends(require_support_head),
    db: Session = Depends(get_db)
):
    """Update SLA resolution hours for a priority level (HIGH, MEDIUM, LOW)."""
    updated = settings_service.update_tat_setting(
        db=db,
        priority=priority.upper(),
        tat_hours=data.tat_hours,
        admin_id=current_user.id
    )
    return TATSettingOut.model_validate(updated)

@router.get("/system-settings", response_model=SystemSettingOut)
def get_system_settings(
    current_user: User = Depends(require_support_head),
    db: Session = Depends(get_db)
):
    """Retrieve global policy parameters (reopen window, max attempts, auto-close)."""
    setting = settings_service.get_or_create_system_settings(db, admin_id=current_user.id)
    return SystemSettingOut.model_validate(setting)

@router.put("/system-settings", response_model=SystemSettingOut)
def update_system_settings(
    data: SystemSettingUpdate,
    current_user: User = Depends(require_support_head),
    db: Session = Depends(get_db)
):
    """Update global system parameters."""
    updated = settings_service.update_system_settings(
        db=db,
        data=data,
        admin_id=current_user.id
    )
    return SystemSettingOut.model_validate(updated)

@router.post("/run-escalation-check")
def trigger_escalation_check(
    current_user: User = Depends(require_support_head),
    db: Session = Depends(get_db)
):
    """Manually trigger background overdue SLA escalation scanner."""
    escalated = sla_service.check_and_escalate_overdue_tickets(db)
    return {
        "status": "success",
        "scanned_at": sla_service.datetime.now(sla_service.timezone.utc),
        "escalated_count": len(escalated),
        "escalated_ticket_ids": [t.id for t in escalated],
        "escalated_ticket_numbers": [t.ticket_number for t in escalated]
    }
