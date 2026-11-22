from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.config import settings

# SQLite connection args for multithreaded FastAPI handling
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

# Enforce foreign key constraints in SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency that provides an isolated SQLAlchemy database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all tables and register database triggers for immutability."""
    from backend.app.models import (
        User, Category, Ticket, Reply, TicketHistory, TATSetting, SystemSetting
    )
    Base.metadata.create_all(bind=engine)
    
    # Setup SQLite triggers preventing UPDATE and DELETE on TICKET_HISTORY
    if settings.DATABASE_URL.startswith("sqlite"):
        with engine.connect() as conn:
            conn.execute(
                text(
                    """
                    CREATE TRIGGER IF NOT EXISTS trg_ticket_history_no_update
                    BEFORE UPDATE ON ticket_history
                    BEGIN
                        SELECT RAISE(ABORT, 'TICKET_HISTORY is an immutable audit log: updates are strictly prohibited.');
                    END;
                    """
                )
            )
            conn.execute(
                text(
                    """
                    CREATE TRIGGER IF NOT EXISTS trg_ticket_history_no_delete
                    BEFORE DELETE ON ticket_history
                    BEGIN
                        SELECT RAISE(ABORT, 'TICKET_HISTORY is an immutable audit log: deletions are strictly prohibited.');
                    END;
                    """
                )
            )
            conn.commit()
