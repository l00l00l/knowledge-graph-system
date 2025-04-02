# 文件: app/api/api_v1/api.py
from fastapi import APIRouter
from app.api.api_v1.endpoints import entities, relationships, documents, query
from app.api.api_v1.endpoints import graph
from app.api.api_v1.endpoints import entity_types
from app.api.api_v1.endpoints import relationship_types

# 创建APIv1路由
api_router = APIRouter()


# 注册端点路由
api_router.include_router(entities.router, prefix="/entities", tags=["实体"])
api_router.include_router(relationships.router, prefix="/relationships", tags=["关系"])
api_router.include_router(documents.router, prefix="/documents", tags=["文档"])
api_router.include_router(query.router, prefix="/query", tags=["查询"])
api_router.include_router(graph.router, prefix="/graph", tags=["图谱"])
api_router.include_router(entity_types.router, prefix="/entity-types", tags=["实体类型"])
api_router.include_router(relationship_types.router, prefix="/relationship-types", tags=["关系类型"])