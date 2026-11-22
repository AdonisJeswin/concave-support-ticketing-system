from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from backend.app.database import Base

class TATSetting(Base):
    __tablename__ = "tat_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    priority = Column(String(20), unique=True, nullable=False)
    tat_hours = Column(Integer, nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        CheckConstraint("priority IN ('LOW', 'MEDIUM', 'HIGH')", name="chk_tat_priority"),
        CheckConstraint("tat_hours > 0", name="chk_tat_hours_positive"),
    )

    updater = relationship("User")

class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, nullable=False)
    reopen_window_days = Column(Integer, default=7, nullable=False)
    max_reopen_attempts = Column(Integer, default=2, nullable=False)
    auto_close_days = Column(Integer, default=7, nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        CheckConstraint("id = 1", name="chk_system_settings_singleton"),
        CheckConstraint("reopen_window_days > 0", name="chk_reopen_window_days_positive"),
        CheckConstraint("max_reopen_attempts >= 0", name="chk_max_reopen_attempts_nonnegative"),
        CheckConstraint("auto_close_days IS NULL OR auto_close_days > 0", name="chk_auto_close_days_positive"),
    )

    updater = relationship("User")
