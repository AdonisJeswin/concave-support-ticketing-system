from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_number = Column(String(32), unique=True, index=True, nullable=False)
    member_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    assigned_agent_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    subject = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="OPEN")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    due_at = Column(DateTime, index=True, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    reopen_count = Column(Integer, default=0, nullable=False)
    tat_paused_at = Column(DateTime, nullable=True)
    total_paused_seconds = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        CheckConstraint("priority IN ('LOW', 'MEDIUM', 'HIGH')", name="chk_ticket_priority"),
        CheckConstraint(
            "status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', 'REOPENED', 'ESCALATED')",
            name="chk_ticket_status"
        ),
        CheckConstraint("reopen_count >= 0", name="chk_ticket_reopen_count"),
        CheckConstraint("total_paused_seconds >= 0", name="chk_ticket_total_paused_seconds"),
        Index("idx_tickets_status_due_at", "status", "due_at"),
        Index("idx_tickets_assigned_agent", "assigned_agent_id", "status"),
        Index("idx_tickets_member_created", "member_id", "created_at"),
    )

    # Relationships
    member = relationship("User", back_populates="tickets_raised", foreign_keys=[member_id])
    assigned_agent = relationship("User", back_populates="tickets_assigned", foreign_keys=[assigned_agent_id])
    category = relationship("Category", back_populates="tickets")
    replies = relationship("Reply", back_populates="ticket", cascade="all, delete-orphan", order_by="Reply.created_at.asc()")
    history = relationship("TicketHistory", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketHistory.created_at.asc()")
