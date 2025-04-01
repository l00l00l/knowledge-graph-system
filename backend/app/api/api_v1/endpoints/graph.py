from typing import Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException
from app.db.neo4j_db import Neo4jDatabase
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
        
        # 更详细的错误处理
        try:
            # 创建会话并执行查询
            async with db.driver.session(database=db.database) as session:
                # 执行实体查询
                nodes_result = await session.run(entity_query)
                nodes_data = await nodes_result.data()
                
                # 执行关系查询
                links_result = await session.run(relation_query)
                links_data = await links_result.data()
        except Exception as session_error:
            print(f"Neo4j session error: {session_error}")
            raise HTTPException(status_code=500, detail=f"Database query error: {str(session_error)}")
        
        # 处理结果
        nodes = [
            {
                "id": node.get("id", f"unknown-{i}"),
                "name": node.get("name", "Unnamed Entity"),
                "type": node.get("type", "entity"),
                "description": node.get("description", "")
            }
            for i, node in enumerate(nodes_data)
        ]
        
        links = [
            {
                "id": link.get("id", f"rel-{i}"),
                "source": link.get("source"),
                "target": link.get("target"),
                "type": link.get("type", "RELATED")
            }
            for i, link in enumerate(links_data)
            if link.get("source") and link.get("target")  # Only include links with valid source/target
        ]
        
        print(f"Returning {len(nodes)} nodes and {len(links)} relationships")
        return {
            "nodes": nodes,
            "links": links
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error retrieving knowledge graph: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving knowledge graph: {str(e)}")