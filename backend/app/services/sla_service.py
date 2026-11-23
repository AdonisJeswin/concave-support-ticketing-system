from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.ticket import Ticket
from backend.app.models.settings import TATSetting, SystemSetting
from backend.app.services.audit_service import log_ticket_action
from backend.app.config import settings

def get_tat_hours_for_priority(db: Session, priority: str) -> int:
    """Retrieve configured TAT hours from database or use baseline defaults."""
    setting = db.query(TATSetting).filter(TATSetting.priority == priority).first()
    if setting:
        return setting.tat_hours
    
    defaults = {
        "HIGH": settings.DEFAULT_TAT_HIGH,
        "MEDIUM": settings.DEFAULT_TAT_MEDIUM,
        "LOW": settings.DEFAULT_TAT_LOW,
    }
    return defaults.get(priority, 24)

def calculate_initial_deadline(db: Session, priority: str, created_at: datetime) -> datetime:
    """Continuous 24/7 SLA calculation: due_at = created_at + tat_hours."""
    tat_hours = get_tat_hours_for_priority(db, priority)
    return created_at + timedelta(hours=tat_hours)

def pause_ticket_tat(db: Session, ticket: Ticket, actor_id: int) -> bool:
    """Pause SLA countdown when agent requests information from member."""
    if ticket.tat_paused_at is not None:
        return False  # Already paused
    
    now = datetime.now(timezone.utc)
    ticket.tat_paused_at = now
    
    log_ticket_action(
        db=db,
        ticket_id=ticket.id,
        action="TAT_PAUSE",
        actor_id=actor_id,
        reason="Agent requested additional information from member; SLA clock paused"
    )
    return True

def resume_ticket_tat(db: Session, ticket: Ticket, actor_id: Optional[int] = None) -> bool:
    """Resume SLA countdown when member responds to ticket."""
    if ticket.tat_paused_at is None:
        return False  # Not paused
    
    now = datetime.now(timezone.utc)
    # Ensure timezone awareness
    paused_at = ticket.tat_paused_at.replace(tzinfo=timezone.utc) if ticket.tat_paused_at.tzinfo is None else ticket.tat_paused_at
    pause_duration = max(0, int((now - paused_at).total_seconds()))
    
    ticket.total_paused_seconds += pause_duration
    ticket.due_at = ticket.due_at + timedelta(seconds=pause_duration)
    ticket.tat_paused_at = None
    
    log_ticket_action(
        db=db,
        ticket_id=ticket.id,
        action="TAT_RESUME",
        actor_id=actor_id,
        reason=f"Member responded; SLA clock resumed after {pause_duration} seconds pause"
    )
    
    # Boundary check: If ticket was already overdue before pause, ensure status reflects breach
    due_at = ticket.due_at.replace(tzinfo=timezone.utc) if ticket.due_at.tzinfo is None else ticket.due_at
    if due_at <= now and ticket.status not in ("RESOLVED", "CLOSED", "ESCALATED"):
        prev_status = ticket.status
        ticket.status = "ESCALATED"
        log_ticket_action(
            db=db,
            ticket_id=ticket.id,
            action="ESCALATED",
            actor_id=None,
            old_value=prev_status,
            new_value="ESCALATED",
            reason="Ticket resumed into overdue state without remaining SLA"
        )
    return True

def recalculate_on_priority_change(
    db: Session,
    ticket: Ticket,
    new_priority: str,
    actor_id: int,
    reason: str
) -> Ticket:
    """
    Recalculate due_at preserving active time elapsed.
    Accurately distinguishes between unpaused and currently paused tickets.
    """
    now = datetime.now(timezone.utc)
    created_at = ticket.created_at.replace(tzinfo=timezone.utc) if ticket.created_at.tzinfo is None else ticket.created_at
    old_priority = ticket.priority

    # A. Calculate active elapsed time
    if ticket.tat_paused_at is None:
        active_elapsed = max(0, int((now - created_at).total_seconds()) - ticket.total_paused_seconds)
    else:
        paused_at = ticket.tat_paused_at.replace(tzinfo=timezone.utc) if ticket.tat_paused_at.tzinfo is None else ticket.tat_paused_at
        active_elapsed = max(0, int((paused_at - created_at).total_seconds()) - ticket.total_paused_seconds)

    # B. Compute remaining SLA for new priority
    new_tat_seconds = get_tat_hours_for_priority(db, new_priority) * 3600
    remaining_sla = new_tat_seconds - active_elapsed

    # C. Update deadline and status
    if ticket.tat_paused_at is None:
        ticket.due_at = now + timedelta(seconds=remaining_sla)
        ticket.priority = new_priority
        log_ticket_action(
            db=db,
            ticket_id=ticket.id,
            action="PRIORITY_CHANGE",
            actor_id=actor_id,
            old_value=old_priority,
            new_value=new_priority,
            reason=reason
        )
        if remaining_sla <= 0 and ticket.status not in ("RESOLVED", "CLOSED", "ESCALATED"):
            prev_status = ticket.status
            ticket.status = "ESCALATED"
            log_ticket_action(
                db=db,
                ticket_id=ticket.id,
                action="ESCALATED",
                actor_id=None,
                old_value=prev_status,
                new_value="ESCALATED",
                reason=f"Priority changed to {new_priority} with active time exceeding SLA threshold"
            )
    else:
        # Currently paused: recalculate deadline from pause point; pause duration added on resume
        paused_at = ticket.tat_paused_at.replace(tzinfo=timezone.utc) if ticket.tat_paused_at.tzinfo is None else ticket.tat_paused_at
        ticket.due_at = paused_at + timedelta(seconds=remaining_sla)
        ticket.priority = new_priority
        log_ticket_action(
            db=db,
            ticket_id=ticket.id,
            action="PRIORITY_CHANGE",
            actor_id=actor_id,
            old_value=old_priority,
            new_value=new_priority,
            reason=reason
        )

    return ticket

def check_and_escalate_overdue_tickets(db: Session) -> List[Ticket]:
    """
    Background escalation scanner:
    Identifies all tickets where status NOT IN ('RESOLVED', 'CLOSED', 'ESCALATED')
    AND tat_paused_at IS NULL AND due_at <= CURRENT_TIMESTAMP.
    Writes 'ESCALATED' to TICKET_HISTORY with actor_id = None.
    """
    now = datetime.now(timezone.utc)
    candidates = (
        db.query(Ticket)
        .filter(
            Ticket.status.notin_(["RESOLVED", "CLOSED", "ESCALATED"]),
            Ticket.tat_paused_at.is_(None),
            Ticket.due_at <= now
        )
        .all()
    )

    escalated = []
    for t in candidates:
        prev_status = t.status
        t.status = "ESCALATED"
        log_ticket_action(
            db=db,
            ticket_id=t.id,
            action="ESCALATED",
            actor_id=None,
            old_value=prev_status,
            new_value="ESCALATED",
            reason="Resolution deadline exceeded active SLA threshold"
        )
        escalated.append(t)
    
    if escalated:
        db.commit()
    return escalated

def check_and_autoclose_resolved_tickets(db: Session) -> List[Ticket]:
    """
    Background auto-close scanner:
    Identifies all tickets where status == 'RESOLVED' and resolved_at exceeds auto_close_days.
    Transitions status to 'CLOSED', sets closed_at, and writes 'CLOSED' to TICKET_HISTORY with actor_id = None.
    """
    sys_settings = db.query(SystemSetting).filter(SystemSetting.id == 1).first()
    auto_close_days = sys_settings.auto_close_days if (sys_settings and sys_settings.auto_close_days is not None) else settings.DEFAULT_AUTO_CLOSE_DAYS
    
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=auto_close_days)
    
    candidates = (
        db.query(Ticket)
        .filter(
            Ticket.status == "RESOLVED",
            Ticket.resolved_at.isnot(None),
            Ticket.resolved_at <= cutoff
        )
        .all()
    )
    
    closed = []
    for t in candidates:
        prev_status = t.status
        t.status = "CLOSED"
        t.closed_at = now
        log_ticket_action(
            db=db,
            ticket_id=t.id,
            action="CLOSED",
            actor_id=None,
            old_value=prev_status,
            new_value="CLOSED",
            reason=f"Auto-closed by system scheduler after exceeding {auto_close_days} days in RESOLVED status"
        )
        closed.append(t)
    
    if closed:
        db.commit()
    return closed

def run_periodic_maintenance(db: Session) -> Dict[str, Any]:
    """
    Execute periodic maintenance: overdue ticket escalation and auto-closing resolved tickets.
    """
    escalated = check_and_escalate_overdue_tickets(db)
    closed = check_and_autoclose_resolved_tickets(db)
    return {
        "escalated_count": len(escalated),
        "closed_count": len(closed),
        "escalated_ticket_ids": [t.id for t in escalated],
        "closed_ticket_ids": [t.id for t in closed],
        "closed_tickets": [t.id for t in closed]
    }
