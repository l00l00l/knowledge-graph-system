# backend/app/api/api_v1/endpoints/relationships.py
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from ....db.neo4j_db import Neo4jDatabase
from ....models.relationships.relationship import Relationship

router = APIRouter()

# Neo4j数据库依赖
def get_db():
    db = Neo4jDatabase()
    try:
        yield db
    finally:
        pass


@router.post("/", response_model=Dict[str, str])
def create_relationship(relationship: Relationship, db: Neo4jDatabase = Depends(get_db)) -> Any:
    """创建实体间关系"""
    try:
        relationship_id = db.create_relationship(relationship.dict())
        return {"id": relationship_id, "message": "关系创建成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建关系失败: {str(e)}")


@router.get("/{relationship_id}", response_model=Optional[Dict[str, Any]])
def read_relationship(relationship_id: str, db: Neo4jDatabase = Depends(get_db)) -> Any:
    """获取关系详情"""
    relationship = db.get_relationship_by_id(relationship_id)
    if not relationship:
        raise HTTPException(status_code=404, detail="关系不存在")
    return relationship


@router.get("/entity/{entity_id}", response_model=List[Dict[str, Any]])
def get_entity_relationships(
    entity_id: str, 
    direction: Optional[str] = None,
    relation_type: Optional[str] = None,
    db: Neo4jDatabase = Depends(get_db)
) -> Any:
    """获取与实体相关的所有关系"""
    direction_query = ""
    if direction == "outgoing":
        direction_query = f"MATCH (n)-[r]->(m) WHERE n.uid = '{entity_id}'"
    elif direction == "incoming":
        direction_query = f"MATCH (n)<-[r]-(m) WHERE n.uid = '{entity_id}'"
    else:
        direction_query = f"MATCH (n)-[r]-(m) WHERE n.uid = '{entity_id}'"
    
    type_filter = ""
    if relation_type:
        type_filter = f" AND type(r) = '{relation_type}'"
    
    query = f"{direction_query}{type_filter} RETURN r, startNode(r) as source, endNode(r) as target"
    
    try:
        results = db.execute_cypher(query)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询关系失败: {str(e)}")