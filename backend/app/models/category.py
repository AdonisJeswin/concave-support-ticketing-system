from sqlalchemy import Column, Integer, String, Boolean, CheckConstraint
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    default_priority = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        CheckConstraint("default_priority IN ('LOW', 'MEDIUM', 'HIGH')", name="chk_category_default_priority"),
    )

    # Relationships
    tickets = relationship("Ticket", back_populates="category")
