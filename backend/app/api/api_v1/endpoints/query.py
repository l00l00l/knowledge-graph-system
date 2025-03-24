# 文件: app/api/api_v1/endpoints/query.py
from typing import Dict, Any
from fastapi import APIRouter, Depends
from app.db.neo4j_db import Neo4jDatabase
from app.services.knowledge_query import KnowledgeQueryService
from app.api.deps import get_db

router = APIRouter()


@router.post("/", response_model=Dict[str, Any])
async def query_knowledge_graph(
    query: str,
    db: Neo4jDatabase = Depends(get_db)
):
    """使用自然语言查询知识图谱"""
    # 创建查询服务
    query_service = KnowledgeQueryService(db)
    
    # 执行查询
    result = await query_service.query_by_natural_language(query)
    
    return result