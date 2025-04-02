# 文件: app/api/api_v1/endpoints/entities.py
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.entities.entity import Entity
from app.db.neo4j_db import Neo4jDatabase
from app.api.deps import get_db

router = APIRouter()


@router.get("/", response_model=List[Entity])
async def read_entities(
    skip: int = 0,
    limit: int = 100,
    entity_type: Optional[str] = None,
    name: Optional[str] = Query(None, description="实体名称（支持模糊匹配）"),
    tag: Optional[str] = Query(None, description="标签过滤"),
    db: Neo4jDatabase = Depends(get_db)
):
    """获取实体列表，支持分页和过滤"""
    query = {}
    if entity_type:
        query["type"] = entity_type
    if name:
        query["name"] = name
    if tag:
        query["tag"] = tag
    
    return await db.find(query)


@router.post("/", response_model=Entity)
async def create_entity(
    entity: Entity,
    db: Neo4jDatabase = Depends(get_db)
):
    """创建新实体"""
    return await db.create(entity)


@router.get("/{entity_id}", response_model=Entity)
async def read_entity(
    entity_id: UUID,
    db: Neo4jDatabase = Depends(get_db)
):
    """获取指定ID的实体"""
    entity = await db.read(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.put("/{entity_id}", response_model=Entity)
async def update_entity(
    entity_id: UUID,
    entity: Entity,
    db: Neo4jDatabase = Depends(get_db)
):
    """更新实体"""
    print(f"Updating entity {entity_id}...")
    
    # Make sure the entity ID in path matches the entity object
    if entity.id != entity_id:
        entity.id = entity_id
    
    # Call the database update method
    updated_entity = await db.update(entity_id, entity)
    
    if updated_entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return updated_entity


@router.delete("/{entity_id}", response_model=bool)
async def delete_entity(
    entity_id: UUID,
    db: Neo4jDatabase = Depends(get_db)
):
    """删除实体"""
    success = await db.delete(entity_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entity not found")
    return success


@router.get("/{entity_id}/context", response_model=dict)
async def get_entity_context(
    entity_id: UUID,
    db: Neo4jDatabase = Depends(get_db)
):
    """获取实体的上下文信息（相关实体和关系）"""
    from app.services.knowledge_query import KnowledgeQueryService
    
    # 创建查询服务
    query_service = KnowledgeQueryService(db)
    
    # 获取实体
    entity = await db.read(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # 获取上下文
    context = await query_service.get_entity_context(entity_id)
    
    return {
        "entity": entity,
        "context": context
    }


@router.get("/{entity_id}/trace", response_model=List[dict])
async def trace_entity_knowledge(
    entity_id: UUID,
    db: Neo4jDatabase = Depends(get_db)
):
    """追溯实体知识来源"""
    from app.services.knowledge_query import KnowledgeQueryService
    
    # 创建查询服务
    query_service = KnowledgeQueryService(db)
    
    # 获取实体
    entity = await db.read(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # 获取溯源信息
    traces = await query_service.trace_knowledge(entity_id=entity_id)
    
    return traces
