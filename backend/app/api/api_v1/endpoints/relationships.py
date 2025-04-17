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
    
@router.put("/{relationship_id}/raw-update", response_model=Dict[str, Any])
async def update_relationship_raw(
    relationship_id: UUID,
    raw_data: Dict[str, Any],
    db: Neo4jDatabase = Depends(get_db)
):
    """更新关系原始数据，包括属性和类型"""
    try:
        rel_id = str(relationship_id)
        #print(f"更新关系原始数据，ID: {rel_id}")
        #print(f"接收到的原始数据: {raw_data}")
        
        # 确保有必要的数据
        if "properties" not in raw_data:
            raise HTTPException(status_code=400, detail="Missing properties in raw data")
        
        # 提取properties对象
        properties = raw_data["properties"]
        
        # 获取关系类型，如果存在的话
        rel_type = raw_data.get("type")
        
        # 分两步更新关系：
        # 1. 更新关系属性
        # 2. 如果需要，更新关系类型
        
        async with db.driver.session(database=db.database) as session:
            # 首先更新属性
            props_query = """
            MATCH ()-[r]->()
            WHERE r.id = $id
            SET r = $properties
            RETURN r
            """
            
            result = await session.run(props_query, id=rel_id, properties=properties)
            record = await result.single()
            
            if not record:
                raise HTTPException(status_code=404, detail="Relationship not found")
            
            updated_relationship = record["r"]
            
            # 如果指定了新的关系类型，并且与原类型不同，更新关系类型
            if rel_type:
                # 获取当前关系类型
                current_type_query = """
                MATCH ()-[r]->()
                WHERE r.id = $id
                RETURN type(r) as current_type
                """
                
                type_result = await session.run(current_type_query, id=rel_id)
                type_record = await type_result.single()
                
                if type_record and type_record["current_type"] != rel_type:
                    # 类型需要更新，使用APOC进行关系类型更新
                    # 注意：这需要Neo4j服务器安装APOC扩展
                    update_type_query = """
                    MATCH (source)-[r]->(target)
                    WHERE r.id = $id
                    CALL apoc.refactor.setType(r, $new_type)
                    YIELD input, output
                    RETURN output
                    """
                    
                    try:
                        type_update_result = await session.run(update_type_query, id=rel_id, new_type=rel_type)
                        type_update_record = await type_update_result.single()
                        
                        if type_update_record:
                            print(f"关系类型已更新为: {rel_type}")
                            # 重新获取更新后的关系
                            get_updated_query = """
                            MATCH ()-[r]->()
                            WHERE r.id = $id
                            RETURN r
                            """
                            updated_result = await session.run(get_updated_query, id=rel_id)
                            updated_record = await updated_result.single()
                            if updated_record:
                                updated_relationship = updated_record["r"]
                    except Exception as type_error:
                        print(f"更新关系类型时出错: {type_error}")
                        # 继续执行，因为属性更新已经成功
            
            # 获取更新后关系的完整信息
            complete_query = """
            MATCH (source)-[r]->(target)
            WHERE r.id = $id
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
            
            complete_result = await session.run(complete_query, id=rel_id)
            complete_record = await complete_result.single()
            
            if complete_record:
                return complete_record["completeRelationship"]
            else:
                return dict(updated_relationship)
            
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error updating relationship: {str(e)}")