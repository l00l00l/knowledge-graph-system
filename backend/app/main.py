# 文件: app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from app.api.api_v1.api import api_router
from app.core.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 创建应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
)

# 配置CORS
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 添加API路由
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """根路径响应"""
    return {
        "message": "欢迎使用个人知识图谱系统 API",
        "version": "0.1.0",
        "documentation": f"/docs"
    }


@app.on_event("startup")
async def startup_event():
    """应用启动事件处理"""
    logger.info("初始化应用...")
    
    # 测试Neo4j连接
    from app.core.config import settings
    from app.db.neo4j_db import Neo4jDatabase
    
    db = Neo4jDatabase(
        uri=settings.NEO4J_URI,
        user=settings.NEO4J_USER,
        password=settings.NEO4J_PASSWORD,
        database=settings.NEO4J_DATABASE
    )
    
    try:
        connection_result = await db.test_connection()
        if connection_result:
            logger.info("Neo4j连接测试成功")
        else:
            logger.error("Neo4j连接测试失败!")
    except Exception as e:
        logger.error(f"Neo4j连接测试出错: {e}")
    
    logger.info("应用初始化完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件处理"""
    logger.info("关闭应用...")
    # 这里可以添加清理代码，如关闭连接等
    logger.info("应用已关闭")


# 独立运行时的入口点
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)