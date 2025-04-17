# 文件: app/api/api_v1/endpoints/relationships.py
from typing import Any, Dict, List, Optional
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
    relationship = await db.read_relationship(relationship_id)
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
    # 确保ID匹配
    if relationship.id != relationship_id:
        relationship.id = relationship_id
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

@router.get("/{relationship_id}/raw", response_model=Dict[str, Any])
async def read_relationship_raw(
    relationship_id: UUID,
    db: Neo4jDatabase = Depends(get_db)
):
    """获取指定ID的关系原始数据"""
    try:
        rel_id = str(relationship_id)
        
        # 使用单一查询获取完整的关系信息
        query = """
        MATCH (source)-[r]->(target)
        WHERE r.id = $id
        WITH r, source, target
        RETURN {
          identity: id(r),
          type: type(r),
          start: id(source),
          end: id(target),
          elementId: toString(id(r)),
          startNodeElementId: toString(id(source)),
          endNodeElementId: toString(id(target)),
          properties: r
        } as completeRelationship
        """
        
        async with db.driver.session(database=db.database) as session:
            result = await session.run(query, id=rel_id)
            record = await result.single()
            
            if not record:
                raise HTTPException(status_code=404, detail="Relationship not found")
            
            # 直接从Cypher查询结果中获取完整的数据结构
            complete_data = record["completeRelationship"]
            #print(f"Complete relationship data from query: {complete_data}")
            
            # 进行必要的后处理，确保数据格式正确
            if isinstance(complete_data, dict):
                # 确保properties属性存在
                if "properties" in complete_data and hasattr(complete_data["properties"], "keys"):
                    # 将Neo4j关系对象转换为字典
                    properties = dict(complete_data["properties"])
                    complete_data["properties"] = properties
            
            return complete_data
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching raw relationship: {str(e)}")