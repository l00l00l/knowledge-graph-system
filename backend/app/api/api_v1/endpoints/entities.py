# 文件: app/api/api_v1/endpoints/entities.py
from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.entities.entity import Entity
from app.db.neo4j_db import Neo4jDatabase
from app.api.deps import get_db

router = APIRouter()


# Add to app/api/api_v1/endpoints/entities.py

@router.get("/search", response_model=List[Dict[str, Any]])
async def search_entities(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Neo4jDatabase = Depends(get_db)
):
    """根据名称搜索实体"""
    try:
        # 修改Cypher查询以提高兼容性和性能
        cypher_query = """
        MATCH (n:Entity)
        WHERE toLower(n.name) CONTAINS toLower($search_text)
        RETURN n.id as id, n.name as name, 
               CASE WHEN n.type IS NOT NULL THEN n.type ELSE (CASE 
                   WHEN size([l IN labels(n) WHERE l <> 'Entity']) > 0 
                   THEN [l IN labels(n) WHERE l <> 'Entity'][0] 
                   ELSE 'Entity' END) 
               END as type
        LIMIT $limit
        """
        
        # 执行查询 - 注意这里参数名改为search_text
        async with db.driver.session(database=db.database) as session:
            result = await session.run(cypher_query, search_text=query, limit=limit)
            data = await result.data()
            
            # 确保所有结果的id字段是字符串而不是对象
            for item in data:
                if isinstance(item.get('id'), dict) and 'low' in item['id'] and 'high' in item['id']:
                    item['id'] = str(UUID(int=(item['id']['high'] << 32) | item['id']['low']))
                elif item.get('id') is not None:
                    item['id'] = str(item['id'])
            
            print(f"Search results for '{query}': {len(data)} entities found")
            return data
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error searching entities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching entities: {str(e)}")

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
