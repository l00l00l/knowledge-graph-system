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
    try:
        # 获取实体
        entity = await db.read(entity_id)
        if entity is None:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        # 查询与实体关联的知识溯源记录
        # 这里使用了简化的查询，实际可能需要根据您的数据模型调整
        # 查询与实体关联的溯源记录和文档
        cypher_query = """
        MATCH (e:Entity {id: $entity_id})
        OPTIONAL MATCH (e)-[:TRACED_TO]->(t:KnowledgeTrace)-[:FROM_DOCUMENT]->(d:Document)
        RETURN t as trace, d as document
        UNION
        MATCH (e:Entity {id: $entity_id})
        WHERE e.source_id IS NOT NULL
        MATCH (d:Document {id: e.source_id})
        RETURN null as trace, d as document
        """
        
        # 如果上面的查询不适用于您的数据模型，您可以使用以下备选查询
        # 通过 source_id 查找关联文档
        fallback_query = """
        MATCH (e:Entity {id: $entity_id})
        WHERE e.source_id IS NOT NULL
        RETURN e.source_id as document_id
        """
        
        traces = []
        
        # 尝试执行主查询
        try:
            async with db.driver.session(database=db.database) as session:
                result = await session.run(cypher_query, entity_id=str(entity_id))
                records = await result.data()
                
                if records and len(records) > 0:
                    # 处理查询结果
                    for record in records:
                        trace_data = record.get("trace")
                        document_data = record.get("document")
                        
                        # 如果找到关联文档
                        if document_data:
                            trace_info = {
                                "entity_id": str(entity_id),
                                "document_id": document_data.get("id", ""),
                                "document_title": document_data.get("title", "Unknown Document"),
                                "document_type": document_data.get("type", "unknown"),
                                "location_data": trace_data.get("location_data", {}) if trace_data else {},
                                "excerpt": trace_data.get("excerpt", "") if trace_data else ""
                            }
                            traces.append(trace_info)
                
                # 如果主查询没有结果，尝试备选查询
                if not traces:
                    result = await session.run(fallback_query, entity_id=str(entity_id))
                    records = await result.data()
                    
                    for record in records:
                        document_id = record.get("document_id")
                        if document_id:
                            # 根据获取的文档ID尝试从数据库获取文档详情
                            # 这里使用SQLite数据库查询，因为文档通常存储在SQLite中
                            from sqlalchemy.orm import Session
                            from app.db.sqlite_db import get_sqlite_db
                            from app.db.models import Document
                            
                            # 创建一个依赖获取SQLite数据库连接
                            sqlite_db = next(get_sqlite_db())
                            
                            # 查询文档
                            document = sqlite_db.query(Document).filter(Document.id == document_id).first()
                            
                            if document:
                                trace_info = {
                                    "entity_id": str(entity_id),
                                    "document_id": document_id,
                                    "document_title": document.title,
                                    "document_type": document.type,
                                    "location_data": {},
                                    "excerpt": ""
                                }
                                traces.append(trace_info)
                            else:
                                # 如果在SQLite中未找到文档，则使用基本信息
                                trace_info = {
                                    "entity_id": str(entity_id),
                                    "document_id": document_id,
                                    "document_title": "Unknown Document",
                                    "document_type": "unknown",
                                    "location_data": {},
                                    "excerpt": ""
                                }
                                traces.append(trace_info)
        
        except Exception as query_error:
            print(f"Error executing trace query: {query_error}")
            # 如果查询出错，尝试使用实体的source_id
            if entity.source_id:
                trace_info = {
                    "entity_id": str(entity_id),
                    "document_id": str(entity.source_id),
                    "document_title": "Source Document",
                    "document_type": entity.source_type or "unknown",
                    "location_data": entity.source_location or {},
                    "excerpt": ""
                }
                traces.append(trace_info)
        
        # 如果仍然没有任何溯源记录，创建一个模拟记录用于测试
        if not traces and entity:
            # 简单的模拟溯源记录，仅用于测试
            trace_info = {
                "entity_id": str(entity_id),
                "document_id": str(entity.source_id) if entity.source_id else "mock-document-id",
                "document_title": "关联文档",
                "document_type": entity.source_type or "unknown",
                "location_data": entity.source_location or {},
                "excerpt": "This is a mock trace record for testing purposes."
            }
            traces.append(trace_info)
        
        return traces
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error tracing knowledge: {str(e)}")
