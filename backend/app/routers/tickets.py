from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.schemas.ticket import (
    TicketCreate, TicketOut, TicketDetailOut, TicketPriorityUpdate,
    TicketAssignUpdate, TicketResolve, TicketReopen, TicketEscalationResolve
)
from backend.app.schemas.reply import ReplyCreate, ReplyOut
from backend.app.dependencies import (
    get_current_user, require_member, require_staff, require_support_head
)
from backend.app.services import ticket_service

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])

@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(
    data: TicketCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Raise a new support ticket (assigns atomic ticket number and calculates initial SLA)."""
    ticket = ticket_service.create_ticket(db=db, member_id=current_user.id, data=data)
    return ticket_service._enrich_ticket_out(ticket)

@router.get("", response_model=List[TicketOut])
def list_tickets(
    status: Optional[str] = None,
    category_id: Optional[int] = None,
    priority: Optional[str] = None,
    is_overdue: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List tickets with role-based filtering (Members see own; Agents/Admin see queue)."""
    tickets, _ = ticket_service.list_tickets(
        db=db,
        user=current_user,
        status_filter=status,
        category_id=category_id,
        priority=priority,
        is_overdue=is_overdue,
        search=search,
        skip=skip,
        limit=limit
    )
    return tickets

@router.get("/{ticket_id}", response_model=TicketDetailOut)
def get_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get full ticket details including replies thread and immutable audit history."""
    return ticket_service.get_ticket_detail(db=db, ticket_id=ticket_id, user=current_user)

@router.post("/{ticket_id}/replies", response_model=ReplyOut, status_code=status.HTTP_201_CREATED)
def post_reply(
    ticket_id: int,
    data: ReplyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Post a reply to conversation thread.
    - Member reply automatically resumes TAT if ticket was paused.
    - Agent can set is_waiting_for_member=True to pause SLA countdown.
    """
    reply = ticket_service.add_reply(
        db=db,
        ticket_id=ticket_id,
        sender_user=current_user,
        data=data
    )
    return ReplyOut(
        id=reply.id,
        ticket_id=reply.ticket_id,
        sender_id=reply.sender_id,
        sender_name=current_user.name,
        sender_role=current_user.role,
        message=reply.message,
        created_at=reply.created_at
    )

@router.patch("/{ticket_id}/assign", response_model=TicketOut)
def assign_ticket(
    ticket_id: int,
    data: TicketAssignUpdate,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db)
):
    """Assign or self-claim an ordinary ticket (Agent / Support Head)."""
    ticket = ticket_service.assign_ticket(
        db=db,
        ticket_id=ticket_id,
        new_agent_id=data.assigned_agent_id,
        actor_user=current_user
    )
    return ticket_service._enrich_ticket_out(ticket)

@router.patch("/{ticket_id}/priority", response_model=TicketOut)
def update_priority(
    ticket_id: int,
    data: TicketPriorityUpdate,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db)
):
    """Update ticket priority with mandatory reason (recalculates remaining SLA)."""
    ticket = ticket_service.update_priority(
        db=db,
        ticket_id=ticket_id,
        new_priority=data.priority.value,
        actor_user=current_user,
        reason=data.reason
    )
    return ticket_service._enrich_ticket_out(ticket)

@router.post("/{ticket_id}/resolve", response_model=TicketOut)
def resolve_ticket(
    ticket_id: int,
    data: Optional[TicketResolve] = None,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db)
):
    """Support Agent marks ticket as resolved with summary note."""
    note = data.resolution_note if data else None
    ticket = ticket_service.resolve_ticket(
        db=db,
        ticket_id=ticket_id,
        actor_user=current_user,
        note=note
    )
    return ticket_service._enrich_ticket_out(ticket)

@router.post("/{ticket_id}/close", response_model=TicketOut)
def confirm_close(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Member confirms resolution and marks ticket CLOSED."""
    ticket = ticket_service.confirm_close_ticket(
        db=db,
        ticket_id=ticket_id,
        member_user=current_user
    )
    return ticket_service._enrich_ticket_out(ticket)

@router.post("/{ticket_id}/reopen", response_model=TicketOut)
def reopen_ticket(
    ticket_id: int,
    data: TicketReopen,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Member reopens resolved ticket within 7-day window and max 2 attempts limit."""
    ticket = ticket_service.reopen_ticket(
        db=db,
        ticket_id=ticket_id,
        member_user=current_user,
        reason=data.reason
    )
    return ticket_service._enrich_ticket_out(ticket)

@router.post("/{ticket_id}/reassign-escalated", response_model=TicketOut)
def reassign_escalated(
    ticket_id: int,
    data: TicketEscalationResolve,
    current_user: User = Depends(require_support_head),
    db: Session = Depends(get_db)
):
    """Support Head reviews escalated ticket and returns it to active handling."""
    ticket = ticket_service.reassign_escalated_ticket(
        db=db,
        ticket_id=ticket_id,
        new_agent_id=data.new_agent_id,
        head_user=current_user,
        directive_reason=data.directive_reason
    )
    return ticket_service._enrich_ticket_out(ticket)
