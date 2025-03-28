# 文件: app/api/api_v1/api.py
from fastapi import APIRouter
from app.api.api_v1.endpoints import entities, relationships, documents, query

# 创建APIv1路由
api_router = APIRouter()

# 注册端点路由
api_router.include_router(entities.router, prefix="/entities", tags=["实体"])
api_router.include_router(relationships.router, prefix="/relationships", tags=["关系"])
api_router.include_router(documents.router, prefix="/documents", tags=["文档"])
api_router.include_router(query.router, prefix="/query", tags=["查询"])