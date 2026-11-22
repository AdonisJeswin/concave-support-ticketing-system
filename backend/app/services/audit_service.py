from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from backend.app.models.history import TicketHistory

def log_ticket_action(
    db: Session,
    ticket_id: int,
    action: str,
    actor_id: Optional[int] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    reason: Optional[str] = None
) -> TicketHistory:
    """
    Append an immutable audit entry to TICKET_HISTORY in the active transaction.
    actor_id is NULL for automated system events (e.g. ESCALATED, AUTO_CLOSE).
    """
    history_entry = TicketHistory(
        ticket_id=ticket_id,
        actor_id=actor_id,
        action=action,
        old_value=old_value,
        new_value=new_value,
        reason=reason,
        created_at=datetime.now(timezone.utc)
    )
    db.add(history_entry)
    db.flush()  # Flush within active transaction
    return history_entry
