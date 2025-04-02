from typing import Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException
from app.db.neo4j_db import Neo4jDatabase
from app.api.deps import get_db

router = APIRouter()

@router.get("/test", response_model=Dict[str, Any])
async def test_graph_endpoint():
    """Simple test endpoint to verify the router is accessible"""
    return {"status": "success", "message": "Graph API is working"}

@router.get("", response_model=Dict[str, Any])
async def get_knowledge_graph(db: Neo4jDatabase = Depends(get_db)):
    """获取整个知识图谱数据用于可视化"""
    try:
        print("Graph API called - retrieving knowledge graph data")
        
        # 查询所有实体
        entity_query = """
        MATCH (n) 
        WHERE n:Entity OR any(label in labels(n) WHERE label <> 'Entity')
        RETURN n.id AS id, n.name AS name, labels(n) AS labels, 
               n.description AS description
        LIMIT 100
        """
        
        # 查询所有关系
        relation_query = """
        MATCH (source)-[r]->(target)
        RETURN source.id AS source, target.id AS target, 
               type(r) AS type, r.id AS id
        LIMIT 200
        """
        
        # 执行查询
        async with db.driver.session(database=db.database) as session:
            # 执行实体查询
            print("Executing entity query...")
            nodes_result = await session.run(entity_query)
            nodes_data = await nodes_result.data()
            print(f"Found {len(nodes_data)} nodes")
            
            # 执行关系查询
            print("Executing relationship query...")
            links_result = await session.run(relation_query)
            links_data = await links_result.data()
            print(f"Found {len(links_data)} relationships")
        
        # 处理结果
        nodes = []
        for i, node in enumerate(nodes_data):
            # Extract node type from labels, defaulting to the first non-Entity label or "entity"
            node_type = "entity"
            if "labels" in node and node["labels"]:
                labels = node["labels"]
                if isinstance(labels, list) and len(labels) > 0:
                    for label in labels:
                        if label != "Entity":
                            node_type = label.lower()
                            break
            
            nodes.append({
                "id": node.get("id", f"unknown-{i}"),
                "name": node.get("name", f"Unnamed Entity {i}"),
                "type": node_type,
                "description": node.get("description", "")
            })
        
        links = []
        for i, link in enumerate(links_data):
            if link.get("source") and link.get("target"):
                links.append({
                    "id": link.get("id", f"rel-{i}"),
                    "source": link.get("source"),
                    "target": link.get("target"),
                    "type": link.get("type", "RELATED")
                })
        
        print(f"Returning {len(nodes)} nodes and {len(links)} relationships")
        return {
            "nodes": nodes,
            "links": links
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error retrieving knowledge graph: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving knowledge graph: {str(e)}")