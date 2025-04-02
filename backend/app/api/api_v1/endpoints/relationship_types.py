from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.sqlite_db import get_sqlite_db
from app.db.models import RelationshipType
from pydantic import BaseModel

router = APIRouter()

class RelationshipTypeSchema(BaseModel):
    id: Optional[int] = None
    type_code: str
    type_name: str
    category: str
    icon: Optional[str] = None
    color: Optional[str] = None
    
    class Config:
        orm_mode = True

@router.get("/", response_model=List[RelationshipTypeSchema])
def read_relationship_types(
    db: Session = Depends(get_sqlite_db),
    category: Optional[str] = None
):
    """获取关系类型"""
    query = db.query(RelationshipType)
    if category:
        query = query.filter(RelationshipType.category == category)
    return query.all()

@router.get("/categories", response_model=List[str])
def read_relationship_type_categories(db: Session = Depends(get_sqlite_db)):
    """获取关系类型分类"""
    categories = db.query(RelationshipType.category).distinct().all()
    return [c[0] for c in categories]