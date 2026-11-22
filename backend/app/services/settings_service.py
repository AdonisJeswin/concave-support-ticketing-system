from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.ticket import Ticket
from backend.app.models.category import Category
from backend.app.models.settings import TATSetting, SystemSetting
from backend.app.schemas.settings import SystemSettingUpdate, DashboardMetrics
from backend.app.config import settings

def get_or_create_system_settings(db: Session, admin_id: int) -> SystemSetting:
    """Ensure singleton row 1 exists for system settings."""
    setting = db.query(SystemSetting).filter(SystemSetting.id == 1).first()
    if not setting:
        setting = SystemSetting(
            id=1,
            reopen_window_days=settings.DEFAULT_REOPEN_WINDOW_DAYS,
            max_reopen_attempts=settings.DEFAULT_MAX_REOPEN_ATTEMPTS,
            auto_close_days=settings.DEFAULT_AUTO_CLOSE_DAYS,
            updated_by=admin_id,
            updated_at=datetime.now(timezone.utc)
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting

def get_all_tat_settings(db: Session) -> List[TATSetting]:
    """Retrieve all priority TAT duration settings."""
    return db.query(TATSetting).all()

def update_tat_setting(db: Session, priority: str, tat_hours: int, admin_id: int) -> TATSetting:
    """Update or create a priority TAT configuration."""
    setting = db.query(TATSetting).filter(TATSetting.priority == priority).first()
    now = datetime.now(timezone.utc)
    if setting:
        setting.tat_hours = tat_hours
        setting.updated_by = admin_id
        setting.updated_at = now
    else:
        setting = TATSetting(
            priority=priority,
            tat_hours=tat_hours,
            updated_by=admin_id,
            updated_at=now
        )
        db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting

def update_system_settings(db: Session, data: SystemSettingUpdate, admin_id: int) -> SystemSetting:
    """Update global system parameters (reopen window, max attempts, auto close)."""
    setting = get_or_create_system_settings(db, admin_id)
    if data.reopen_window_days is not None:
        setting.reopen_window_days = data.reopen_window_days
    if data.max_reopen_attempts is not None:
        setting.max_reopen_attempts = data.max_reopen_attempts
    if data.auto_close_days is not None:
        setting.auto_close_days = data.auto_close_days
    setting.updated_by = admin_id
    setting.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(setting)
    return setting

def get_dashboard_metrics(db: Session) -> DashboardMetrics:
    """Calculate executive dashboard metrics for Support Head."""
    now = datetime.now(timezone.utc)
    
    # Total open tickets
    total_open = db.query(Ticket).filter(
        Ticket.status.in_(["OPEN", "IN_PROGRESS", "REOPENED", "ESCALATED"])
    ).count()

    # Overdue tickets
    overdue_count = db.query(Ticket).filter(
        Ticket.status.notin_(["RESOLVED", "CLOSED"]),
        Ticket.due_at <= now
    ).count()

    # Escalated tickets
    escalated_count = db.query(Ticket).filter(Ticket.status == "ESCALATED").count()

    # Resolved today (UTC calendar day)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    resolved_today = db.query(Ticket).filter(
        Ticket.status.in_(["RESOLVED", "CLOSED"]),
        Ticket.resolved_at >= today_start
    ).count()

    # Average Resolution Time (ART) in hours
    resolved_tickets = db.query(Ticket).filter(Ticket.resolved_at.isnot(None)).all()
    if resolved_tickets:
        total_seconds = 0
        for t in resolved_tickets:
            created = t.created_at.replace(tzinfo=timezone.utc) if t.created_at.tzinfo is None else t.created_at
            resolved = t.resolved_at.replace(tzinfo=timezone.utc) if t.resolved_at.tzinfo is None else t.resolved_at
            duration = max(0, (resolved - created).total_seconds() - t.total_paused_seconds)
            total_seconds += duration
        art_hours = round((total_seconds / len(resolved_tickets)) / 3600.0, 2)
    else:
        art_hours = 0.0

    # Category breakdown
    cat_counts = (
        db.query(Category.name, func.count(Ticket.id))
        .outerjoin(Ticket, Ticket.category_id == Category.id)
        .group_by(Category.name)
        .all()
    )
    category_breakdown = {name: count for name, count in cat_counts}

    return DashboardMetrics(
        total_open_tickets=total_open,
        overdue_tickets_count=overdue_count,
        escalated_tickets_count=escalated_count,
        resolved_today_count=resolved_today,
        average_resolution_time_hours=art_hours,
        category_breakdown=category_breakdown
    )
