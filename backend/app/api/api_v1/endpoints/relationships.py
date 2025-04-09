# 文件: app/api/api_v1/endpoints/relationships.py
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.relationships.relationship import Relationship
from app.db.neo4j_db import Neo4jDatabase
from app.api.deps import get_db

router = APIRouter()


@router.get("/", response_model=List[Relationship])
async def read_relationships(
    skip: int = 0,
    limit: int = 100,
    relationship_type: Optional[str] = None,
    source_id: Optional[UUID] = None,
    target_id: Optional[UUID] = None,
    db: Neo4jDatabase = Depends(get_db)
):
    """获取关系列表，支持分页和过滤"""
    query = {}
    if relationship_type:
        query["type"] = relationship_type
    if source_id:
        query["source_id"] = source_id
    if target_id:
        query["target_id"] = target_id
    
    return await db.find(query)


@router.post("/", response_model=Relationship)
async def create_relationship(
    relationship: Relationship,
    db: Neo4jDatabase = Depends(get_db)
):
    """创建新关系"""
    return await db.create(relationship)


@router.get("/{relationship_id}", response_model=Relationship)
async def read_relationship(
    relationship_id: UUID,
    db: Neo4jDatabase = Depends(get_db)
):
    """获取指定ID的关系"""
    relationship = await db.read(relationship_id)
    if relationship is None:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return relationship


@router.put("/{relationship_id}", response_model=Relationship)
async def update_relationship(
    relationship_id: UUID,
    relationship: Relationship,
    db: Neo4jDatabase = Depends(get_db)
):
    """更新关系"""
    updated_relationship = await db.update(relationship_id, relationship)
    if updated_relationship is None:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return updated_relationship


@router.delete("/{relationship_id}", response_model=bool)
async def delete_relationship(
    relationship_id: UUID,
    db: Neo4jDatabase = Depends(get_db)
):
    """删除关系"""
    success = await db.delete_relationship(relationship_id)
    if not success:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return success


@router.get("/{relationship_id}/trace", response_model=List[dict])
async def trace_relationship_knowledge(
    relationship_id: UUID,
    db: Neo4jDatabase = Depends(get_db)
):
    """追溯关系知识来源"""
    from app.services.knowledge_query import KnowledgeQueryService
    
    # 创建查询服务
    query_service = KnowledgeQueryService(db)
    
    # 获取关系
    relationship = await db.read(relationship_id)
    if relationship is None:
        raise HTTPException(status_code=404, detail="Relationship not found")
    
    # 获取溯源信息
    traces = await query_service.trace_knowledge(relationship_id=relationship_id)
    
    return traces

