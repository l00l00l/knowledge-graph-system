# app/core/application.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api_v1.api import api_router
from app.core.config import settings
from app.core.dependencies import get_db, get_document_processor, get_knowledge_extractor
from app.core.dependencies import get_query_service, get_provenance_service, get_nlp_service


def create_application() -> FastAPI:
    """应用工厂函数，创建并配置FastAPI应用"""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="个人知识图谱构建与查询系统",
        version="0.1.0",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册API路由
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    
    # 启动事件
    @app.on_event("startup")
    async def startup_event():
        # 这里可以添加启动时需要执行的代码
        # 例如，初始化数据库连接池、加载NLP模型等
        pass
    
    # 关闭事件
    @app.on_event("shutdown")
    async def shutdown_event():
        # 这里可以添加关闭时需要执行的代码
        # 例如，关闭数据库连接池等
        pass
    
    return app