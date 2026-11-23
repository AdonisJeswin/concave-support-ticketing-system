from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc, func
from fastapi import HTTPException, status
from backend.app.models.ticket import Ticket
from backend.app.models.category import Category
from backend.app.models.user import User
from backend.app.models.reply import Reply
from backend.app.models.history import TicketHistory
from backend.app.models.settings import SystemSetting
from backend.app.schemas.ticket import TicketCreate, TicketOut, TicketDetailOut
from backend.app.schemas.reply import ReplyCreate, ReplyOut
from backend.app.schemas.history import HistoryOut
from backend.app.services.audit_service import log_ticket_action
from backend.app.services.sla_service import (
    calculate_initial_deadline,
    pause_ticket_tat,
    resume_ticket_tat,
    recalculate_on_priority_change,
    get_tat_hours_for_priority
)
from backend.app.services.settings_service import get_or_create_system_settings

def generate_ticket_number(db: Session) -> str:
    """Generate sequential, zero-padded ticket identifier like TKT-0042."""
    max_id = db.query(func.max(Ticket.id)).scalar() or 0
    next_id = max_id + 1
    return f"TKT-{next_id:04d}"

def _enrich_ticket_out(t: Ticket) -> TicketOut:
    """Calculate dynamic fields like is_overdue, is_paused, remaining_sla_seconds."""
    now = datetime.now(timezone.utc)
    due_at = t.due_at.replace(tzinfo=timezone.utc) if t.due_at.tzinfo is None else t.due_at
    
    is_paused = t.tat_paused_at is not None
    is_overdue = (due_at <= now) and (t.status not in ("RESOLVED", "CLOSED"))
    
    if is_paused:
        paused_at = t.tat_paused_at.replace(tzinfo=timezone.utc) if t.tat_paused_at.tzinfo is None else t.tat_paused_at
        remaining = int((due_at - paused_at).total_seconds())
    else:
        remaining = int((due_at - now).total_seconds())
    
    return TicketOut(
        id=t.id,
        ticket_number=t.ticket_number,
        member_id=t.member_id,
        member_name=t.member.name if t.member else None,
        member_email=t.member.email if t.member else None,
        category_id=t.category_id,
        category_name=t.category.name if t.category else None,
        assigned_agent_id=t.assigned_agent_id,
        assigned_agent_name=t.assigned_agent.name if t.assigned_agent else None,
        subject=t.subject,
        description=t.description,
        priority=t.priority,
        status=t.status,
        created_at=t.created_at,
        due_at=t.due_at,
        resolved_at=t.resolved_at,
        closed_at=t.closed_at,
        reopen_count=t.reopen_count,
        tat_paused_at=t.tat_paused_at,
        total_paused_seconds=t.total_paused_seconds,
        is_overdue=is_overdue,
        is_paused=is_paused,
        remaining_sla_seconds=remaining
    )

def create_ticket(db: Session, member_id: int, data: TicketCreate) -> Ticket:
    """Create a new ticket with automatic default priority and initial 24/7 SLA."""
    category = db.query(Category).filter(Category.id == data.category_id, Category.is_active.is_(True)).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected category is invalid or inactive")

    now = datetime.now(timezone.utc)
    priority = category.default_priority
    due_at = calculate_initial_deadline(db, priority, now)
    ticket_num = generate_ticket_number(db)

    ticket = Ticket(
        ticket_number=ticket_num,
        member_id=member_id,
        category_id=category.id,
        subject=data.subject.strip(),
        description=data.description.strip(),
        priority=priority,
        status="OPEN",
        created_at=now,
        due_at=due_at,
        reopen_count=0,
        total_paused_seconds=0
    )
    db.add(ticket)
    db.flush()

    # Log initial creation audit
    log_ticket_action(
        db=db,
        ticket_id=ticket.id,
        action="CREATED",
        actor_id=member_id,
        new_value="OPEN",
        reason=f"Ticket created under category '{category.name}' with default priority '{priority}'"
    )
    db.commit()
    db.refresh(ticket)
    return ticket

def list_tickets(
    db: Session,
    user: User,
    status_filter: Optional[str] = None,
    category_id: Optional[int] = None,
    priority: Optional[str] = None,
    is_overdue: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50
) -> Tuple[List[TicketOut], int]:
    """Query tickets with role isolation, filters, and search capabilities."""
    query = db.query(Ticket).options(
        joinedload(Ticket.member),
        joinedload(Ticket.assigned_agent),
        joinedload(Ticket.category)
    )

    # Role enforcement
    if user.role == "MEMBER":
        query = query.filter(Ticket.member_id == user.id)

    # Filters
    if status_filter:
        query = query.filter(Ticket.status == status_filter)
    if category_id:
        query = query.filter(Ticket.category_id == category_id)
    if priority:
        query = query.filter(Ticket.priority == priority)
    
    now = datetime.now(timezone.utc)
    if is_overdue is True:
        query = query.filter(
            Ticket.due_at <= now,
            Ticket.status.notin_(["RESOLVED", "CLOSED"])
        )
    elif is_overdue is False:
        query = query.filter(
            or_(
                Ticket.due_at > now,
                Ticket.status.in_(["RESOLVED", "CLOSED"])
            )
        )

    # Search
    if search:
        search_term = f"%{search.strip()}%"
        query = query.join(User, Ticket.member_id == User.id).filter(
            or_(
                Ticket.ticket_number.ilike(search_term),
                Ticket.subject.ilike(search_term),
                User.name.ilike(search_term),
                User.email.ilike(search_term)
            )
        )

    total = query.count()
    tickets = query.order_by(desc(Ticket.created_at)).offset(skip).limit(limit).all()
    
    return [_enrich_ticket_out(t) for t in tickets], total

def get_ticket_detail(db: Session, ticket_id: int, user: User) -> TicketDetailOut:
    """Retrieve full ticket detail including thread messages and complete audit trail."""
    ticket = (
        db.query(Ticket)
        .options(
            joinedload(Ticket.member),
            joinedload(Ticket.assigned_agent),
            joinedload(Ticket.category),
            joinedload(Ticket.replies).joinedload(Reply.sender),
            joinedload(Ticket.history).joinedload(TicketHistory.actor)
        )
        .filter(Ticket.id == ticket_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    # Member can only view own tickets
    if user.role == "MEMBER" and ticket.member_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this ticket")

    base_out = _enrich_ticket_out(ticket)

    # Map replies
    replies_out = [
        ReplyOut(
            id=r.id,
            ticket_id=r.ticket_id,
            sender_id=r.sender_id,
            sender_name=r.sender.name if r.sender else "Unknown",
            sender_role=r.sender.role if r.sender else "Unknown",
            message=r.message,
            created_at=r.created_at
        )
        for r in ticket.replies
    ]

    # Map history
    history_out = [
        HistoryOut(
            id=h.id,
            ticket_id=h.ticket_id,
            actor_id=h.actor_id,
            actor_name=h.actor.name if h.actor else "System Automated Agent",
            action=h.action,
            old_value=h.old_value,
            new_value=h.new_value,
            reason=h.reason,
            created_at=h.created_at
        )
        for h in ticket.history
    ]

    return TicketDetailOut(
        **base_out.model_dump(),
        replies=replies_out,
        history=history_out
    )

def assign_ticket(db: Session, ticket_id: int, new_agent_id: Optional[int], actor_user: User) -> Ticket:
    """Assign or reassign an ordinary ticket."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    
    if ticket.status == "ESCALATED" and actor_user.role != "SUPPORT_HEAD":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Escalated tickets can only be reassigned and reviewed by Support Head"
        )

    old_agent_name = ticket.assigned_agent.name if ticket.assigned_agent else "Unassigned"
    
    if new_agent_id:
        new_agent = db.query(User).filter(User.id == new_agent_id, User.role.in_(["AGENT", "SUPPORT_HEAD"])).first()
        if not new_agent:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected agent is invalid")
        new_agent_name = new_agent.name
    else:
        new_agent_name = "Unassigned"

    ticket.assigned_agent_id = new_agent_id
    if ticket.status == "OPEN" and new_agent_id is not None:
        ticket.status = "IN_PROGRESS"
        log_ticket_action(
            db=db,
            ticket_id=ticket.id,
            action="STATUS_CHANGE",
            actor_id=actor_user.id,
            old_value="OPEN",
            new_value="IN_PROGRESS",
            reason=f"Claimed by agent {new_agent_name}"
        )

    log_ticket_action(
        db=db,
        ticket_id=ticket.id,
        action="ASSIGNED",
        actor_id=actor_user.id,
        old_value=old_agent_name,
        new_value=new_agent_name,
        reason=f"Ticket assigned by {actor_user.name}"
    )
    db.commit()
    db.refresh(ticket)
    return ticket

def reassign_escalated_ticket(
    db: Session,
    ticket_id: int,
    new_agent_id: int,
    head_user: User,
    directive_reason: str
) -> Ticket:
    """Support Head reviews escalated ticket and returns it to active agent handling."""
    if head_user.role != "SUPPORT_HEAD":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Support Head can resolve escalations")

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if ticket.status != "ESCALATED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket is not in ESCALATED status")

    if not directive_reason or len(directive_reason.strip()) < 5:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Directive reason must be at least 5 characters")

    new_agent = db.query(User).filter(User.id == new_agent_id, User.role.in_(["AGENT", "SUPPORT_HEAD"])).first()
    if not new_agent:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target agent not found")

    ticket.assigned_agent_id = new_agent_id
    ticket.status = "IN_PROGRESS"

    log_ticket_action(
        db=db,
        ticket_id=ticket.id,
        action="ESCALATION_RESOLVED",
        actor_id=head_user.id,
        old_value="ESCALATED",
        new_value="IN_PROGRESS",
        reason=f"Reassigned to {new_agent.name}: {directive_reason}"
    )
    db.commit()
    db.refresh(ticket)
    return ticket

def update_priority(
    db: Session,
    ticket_id: int,
    new_priority: str,
    actor_user: User,
    reason: str
) -> Ticket:
    """Agent or Admin updates priority with mandatory audit explanation."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if ticket.status in ("RESOLVED", "CLOSED"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot alter priority on resolved or closed tickets")

    if ticket.priority == new_priority:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket already has this priority")

    if not reason or len(reason.strip()) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Priority change requires a mandatory explanation of at least 5 characters"
        )

    recalculate_on_priority_change(
        db=db,
        ticket=ticket,
        new_priority=new_priority,
        actor_id=actor_user.id,
        reason=reason
    )
    db.commit()
    db.refresh(ticket)
    return ticket

def resolve_ticket(db: Session, ticket_id: int, actor_user: User, note: Optional[str] = None) -> Ticket:
    """Agent or Admin marks ticket as resolved."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if ticket.status in ("RESOLVED", "CLOSED"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket is already resolved or closed")

    now = datetime.now(timezone.utc)
    prev_status = ticket.status

    # If ticket was paused, clear pause and record paused interval
    if ticket.tat_paused_at is not None:
        paused_at = ticket.tat_paused_at.replace(tzinfo=timezone.utc) if ticket.tat_paused_at.tzinfo is None else ticket.tat_paused_at
        ticket.total_paused_seconds += max(0, int((now - paused_at).total_seconds()))
        ticket.tat_paused_at = None

    ticket.status = "RESOLVED"
    ticket.resolved_at = now

    reason = f"Resolution summary: {note}" if note else "Issue confirmed resolved by agent"
    log_ticket_action(
        db=db,
        ticket_id=ticket.id,
        action="RESOLVED",
        actor_id=actor_user.id,
        old_value=prev_status,
        new_value="RESOLVED",
        reason=reason
    )
    db.commit()
    db.refresh(ticket)
    return ticket

def confirm_close_ticket(db: Session, ticket_id: int, member_user: User) -> Ticket:
    """Member confirms resolution and closes ticket."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if member_user.role == "MEMBER" and ticket.member_id != member_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if ticket.status != "RESOLVED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only RESOLVED tickets can be closed by member")

    now = datetime.now(timezone.utc)
    ticket.status = "CLOSED"
    ticket.closed_at = now

    log_ticket_action(
        db=db,
        ticket_id=ticket.id,
        action="CLOSED",
        actor_id=member_user.id,
        old_value="RESOLVED",
        new_value="CLOSED",
        reason="Member confirmed satisfactory resolution"
    )
    db.commit()
    db.refresh(ticket)
    return ticket

def reopen_ticket(db: Session, ticket_id: int, member_user: User, reason: str) -> Ticket:
    """Member reopens resolved ticket within the approved 7-day, 2-attempt window."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if member_user.role == "MEMBER" and ticket.member_id != member_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if ticket.status != "RESOLVED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reopen ticket in '{ticket.status}' status. Only RESOLVED tickets are eligible."
        )

    if not reason or len(reason.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A descriptive reason of at least 10 characters is mandatory to reopen a ticket."
        )

    sys_settings = get_or_create_system_settings(db, admin_id=1)
    now = datetime.now(timezone.utc)
    resolved_at = ticket.resolved_at.replace(tzinfo=timezone.utc) if ticket.resolved_at.tzinfo is None else ticket.resolved_at

    # Check 1: 7-day window
    window_limit = timedelta(days=sys_settings.reopen_window_days)
    if (now - resolved_at) > window_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Reopening window of {sys_settings.reopen_window_days} days has expired."
        )

    # Check 2: Max attempts
    if ticket.reopen_count >= sys_settings.max_reopen_attempts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum reopen attempts ({sys_settings.max_reopen_attempts}) reached for this ticket."
        )

    # Reopen ticket
    ticket.reopen_count += 1
    ticket.status = "REOPENED"
    
    # Recalculate fresh TAT window for reopened inquiry
    tat_hours = get_tat_hours_for_priority(db, ticket.priority)
    ticket.due_at = now + timedelta(hours=tat_hours)

    log_ticket_action(
        db=db,
        ticket_id=ticket.id,
        action="REOPENED",
        actor_id=member_user.id,
        old_value="RESOLVED",
        new_value="REOPENED",
        reason=f"Attempt {ticket.reopen_count}/{sys_settings.max_reopen_attempts}: {reason}"
    )
    db.commit()
    db.refresh(ticket)
    return ticket

def add_reply(
    db: Session,
    ticket_id: int,
    sender_user: User,
    data: ReplyCreate
) -> Reply:
    """Post message in ticket conversation thread with stateful Waiting-for-Member handling."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if sender_user.role == "MEMBER" and ticket.member_id != sender_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if ticket.status == "CLOSED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot reply to a closed ticket")

    now = datetime.now(timezone.utc)
    reply = Reply(
        ticket_id=ticket.id,
        sender_id=sender_user.id,
        message=data.message.strip(),
        created_at=now
    )
    db.add(reply)

    # Stateful TAT pause / resume logic
    if sender_user.role == "MEMBER":
        # Member replying resumes clock if paused
        if ticket.tat_paused_at is not None:
            resume_ticket_tat(db=db, ticket=ticket, actor_id=sender_user.id)
    else:
        # Agent or Admin replying
        if data.is_waiting_for_member and ticket.tat_paused_at is None:
            pause_ticket_tat(db=db, ticket=ticket, actor_id=sender_user.id)

    db.commit()
    db.refresh(reply)
    return reply
