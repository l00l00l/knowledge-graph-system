# 文件: app/api/deps.py
from typing import Generator
from app.db.neo4j_db import Neo4jDatabase
from app.core.config import settings


async def get_db() -> Generator:
    """获取数据库连接"""
    db = Neo4jDatabase(
        uri=settings.NEO4J_URI,
        user=settings.NEO4J_USER,
        password=settings.NEO4J_PASSWORD,
        database=settings.NEO4J_DATABASE
    )
    try:
        yield db
    finally:
        await db.close()
