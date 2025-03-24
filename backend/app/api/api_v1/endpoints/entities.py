# backend/app/api/api_v1/endpoints/entities.py
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ....db.neo4j_db import Neo4jDatabase
from ....models.entities.entity import Entity

router = APIRouter()

# Neo4j数据库依赖
def get_db():
    db = Neo4jDatabase()
    try:
        yield db
    finally:
        # 在这里可以添加清理逻辑如果需要
        pass


@router.post("/", response_model=Dict[str, str])
def create_entity(entity: Entity, db: Neo4jDatabase = Depends(get_db)) -> Any:
    """创建新实体"""
    try:
        entity_id = db.create_entity(entity.dict())
        return {"id": entity_id, "message": "实体创建成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建实体失败: {str(e)}")


@router.get("/{entity_id}", response_model=Optional[Dict[str, Any]])
def read_entity(entity_id: str, db: Neo4jDatabase = Depends(get_db)) -> Any:
    """获取实体详情"""
    entity = db.get_entity_by_id(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="实体不存在")
    return entity


@router.get("/", response_model=List[Dict[str, Any]])
def search_entities(
    name: Optional[str] = None,
    label: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = Query(100, gt=0, le=1000),
    db: Neo4jDatabase = Depends(get_db)
) -> Any:
    """搜索实体"""
    query = {}
    if name:
        query["name"] = name
    if label:
        query["label"] = label
    if tag:
        # Neo4j需要特殊处理标签查询，这里简化处理
        query["tags"] = tag
    
    try:
        entities = db.search_entities(query, limit)
        return entities
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询实体失败: {str(e)}")