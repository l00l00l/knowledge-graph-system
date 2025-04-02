from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.sqlite_db import get_sqlite_db
from app.db.models import EntityType
from pydantic import BaseModel

router = APIRouter()

class EntityTypeSchema(BaseModel):
    id: Optional[int] = None
    type_code: str
    type_name: str
    category: str
    icon: Optional[str] = None
    color: Optional[str] = None
    
    class Config:
        orm_mode = True

@router.get("/", response_model=List[EntityTypeSchema])
def read_entity_types(
    db: Session = Depends(get_sqlite_db),
    category: Optional[str] = None
):
    """获取实体类型"""
    query = db.query(EntityType)
    if category:
        query = query.filter(EntityType.category == category)
    return query.all()

@router.get("/categories", response_model=List[str])
def read_entity_type_categories(db: Session = Depends(get_sqlite_db)):
    """获取实体类型分类"""
    categories = db.query(EntityType.category).distinct().all()
    return [c[0] for c in categories]

@router.post("/", response_model=EntityTypeSchema)
def create_entity_type(entity_type: EntityTypeSchema, db: Session = Depends(get_sqlite_db)):
    """创建新实体类型"""
    db_entity_type = EntityType(
        type_code=entity_type.type_code,
        type_name=entity_type.type_name,
        icon=entity_type.icon,
        color=entity_type.color
    )
    db.add(db_entity_type)
    db.commit()
    db.refresh(db_entity_type)
    return db_entity_type