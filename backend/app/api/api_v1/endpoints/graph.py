from typing import Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException
from app.db.neo4j_enhanced import Neo4jEnhanced
from app.api.deps import get_db

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
async def get_knowledge_graph(db: Neo4jDatabase = Depends(get_db)):
    """获取整个知识图谱数据用于可视化"""
    try:
        # 查询所有实体
        entity_query = """
        MATCH (n:Entity) 
        RETURN n.id AS id, n.name AS name, n.type AS type, 
               n.description AS description
        LIMIT 100
        """
        
        # 查询所有关系
        relation_query = """
        MATCH (source:Entity)-[r]->(target:Entity)
        RETURN source.id AS source, target.id AS target, 
               type(r) AS type, r.id AS id
        LIMIT 200
        """
        
        # 创建会话并执行查询
        async with db.driver.session(database=db.database) as session:
            # 执行实体查询
            nodes_result = await session.run(entity_query)
            nodes_data = await nodes_result.data()
            
            # 执行关系查询
            links_result = await session.run(relation_query)
            links_data = await links_result.data()
        
        # 处理结果
        nodes = [
            {
                "id": node["id"],
                "name": node["name"],
                "type": node["type"] or "entity",
                "description": node["description"] or ""
            }
            for node in nodes_data
        ]
        
        links = [
            {
                "id": link["id"],
                "source": link["source"],
                "target": link["target"],
                "type": link["type"]
            }
            for link in links_data
        ]
        
        return {
            "nodes": nodes,
            "links": links
        }
    except Exception as e:
        print(f"Error retrieving knowledge graph: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving knowledge graph: {str(e)}")