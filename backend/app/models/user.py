from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, CheckConstraint
from sqlalchemy.orm import relationship
from backend.app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        CheckConstraint("role IN ('MEMBER', 'AGENT', 'SUPPORT_HEAD')", name="chk_user_role"),
    )

    # Relationships
    tickets_raised = relationship("Ticket", back_populates="member", foreign_keys="Ticket.member_id")
    tickets_assigned = relationship("Ticket", back_populates="assigned_agent", foreign_keys="Ticket.assigned_agent_id")
    replies = relationship("Reply", back_populates="sender")
    audit_actions = relationship("TicketHistory", back_populates="actor")
