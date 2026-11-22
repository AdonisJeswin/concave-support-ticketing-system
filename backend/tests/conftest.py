import os
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models import User, Category, TATSetting, SystemSetting
from backend.app.services.auth_service import hash_password, create_access_token

# In-memory SQLite database for isolated test execution
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database schema for every test function."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Seed core entities for testing
    admin = User(
        name="Admin User",
        email="admin@test.com",
        password_hash=hash_password("password123"),
        role="SUPPORT_HEAD",
        created_at=datetime.now(timezone.utc)
    )
    agent = User(
        name="Agent User",
        email="agent@test.com",
        password_hash=hash_password("password123"),
        role="AGENT",
        created_at=datetime.now(timezone.utc)
    )
    member = User(
        name="Member User",
        email="member@test.com",
        password_hash=hash_password("password123"),
        role="MEMBER",
        created_at=datetime.now(timezone.utc)
    )
    other_member = User(
        name="Other Member",
        email="other@test.com",
        password_hash=hash_password("password123"),
        role="MEMBER",
        created_at=datetime.now(timezone.utc)
    )
    db.add_all([admin, agent, member, other_member])
    db.flush()

    # Seed categories
    cats = [
        Category(name="Payment", default_priority="HIGH", is_active=True),
        Category(name="Survey Issue", default_priority="HIGH", is_active=True),
        Category(name="Profile Change", default_priority="MEDIUM", is_active=True),
        Category(name="Eligibility", default_priority="MEDIUM", is_active=True),
        Category(name="Other", default_priority="LOW", is_active=True),
    ]
    db.add_all(cats)

    # Seed TAT Settings
    tat = [
        TATSetting(priority="HIGH", tat_hours=4, updated_by=admin.id),
        TATSetting(priority="MEDIUM", tat_hours=24, updated_by=admin.id),
        TATSetting(priority="LOW", tat_hours=48, updated_by=admin.id),
    ]
    db.add_all(tat)

    # Seed System Settings singleton
    sys_setting = SystemSetting(
        id=1,
        reopen_window_days=7,
        max_reopen_attempts=2,
        auto_close_days=7,
        updated_by=admin.id
    )
    db.add(sys_setting)
    db.commit()

    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

def _get_headers_for(email: str, role: str, user_id: int):
    token = create_access_token({"sub": str(user_id), "role": role})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(db_session):
    u = db_session.query(User).filter(User.email == "admin@test.com").first()
    return _get_headers_for(u.email, u.role, u.id)

@pytest.fixture
def agent_headers(db_session):
    u = db_session.query(User).filter(User.email == "agent@test.com").first()
    return _get_headers_for(u.email, u.role, u.id)

@pytest.fixture
def member_headers(db_session):
    u = db_session.query(User).filter(User.email == "member@test.com").first()
    return _get_headers_for(u.email, u.role, u.id)

@pytest.fixture
def other_member_headers(db_session):
    u = db_session.query(User).filter(User.email == "other@test.com").first()
    return _get_headers_for(u.email, u.role, u.id)
