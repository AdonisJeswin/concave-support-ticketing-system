from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.category import Category
from backend.app.schemas.category import CategoryOut

router = APIRouter(prefix="/api/categories", tags=["Categories"])

@router.get("", response_model=List[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    """List all active inquiry categories with default priority mappings."""
    categories = db.query(Category).filter(Category.is_active.is_(True)).all()
    return [CategoryOut.model_validate(c) for c in categories]
