from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.sqlite_db import get_sqlite_db
from app.db.models import EntityType
from pydantic import BaseModel

router = APIRouter()

class EntityTypeSchema(BaseModel):
    id: int = None
    type_code: str
    type_name: str
    icon: str = None
    color: str = None
    
    class Config:
        orm_mode = True

@router.get("/", response_model=List[EntityTypeSchema])
def read_entity_types(db: Session = Depends(get_sqlite_db)):
    """获取所有实体类型"""
    return db.query(EntityType).all()

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