from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.schemas.user import LoginRequest, MockLoginRequest, TokenResponse, UserOut
from backend.app.services.auth_service import verify_password, create_access_token
from backend.app.dependencies import get_current_user, require_staff

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate with email and password."""
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserOut.model_validate(user)
    )

@router.post("/token", response_model=TokenResponse)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 compatible token login for Swagger UI documentation."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserOut.model_validate(user)
    )

@router.post("/mock-login", response_model=TokenResponse)
def mock_login(request: MockLoginRequest, db: Session = Depends(get_db)):
    """
    Mock login enabling seamless switching between MEMBER, AGENT, and SUPPORT_HEAD roles
    for evaluation and workflow demonstration.
    """
    query = db.query(User).filter(User.role == request.role.value)
    if request.email:
        query = query.filter(User.email == request.email)
    
    user = query.first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No user found for role '{request.role.value}'. Please run the database seed script."
        )

    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserOut.model_validate(user)
    )

@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    """Return currently authenticated user profile."""
    return UserOut.model_validate(current_user)

@router.get("/agents", response_model=List[UserOut])
def get_support_agents(current_user: User = Depends(require_staff), db: Session = Depends(get_db)):
    """Retrieve list of active support agents for ticket assignment dropdowns."""
    return db.query(User).filter(User.role == "AGENT").order_by(User.name.asc()).all()

