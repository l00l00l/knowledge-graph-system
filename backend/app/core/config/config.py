# backend/app/core/config.py
import os
from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础设置
    APP_NAME: str = "个人知识图谱系统"
    APP_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"
    DEBUG: bool = True
    
    # 安全设置
    SECRET_KEY: str = "请修改这个密钥在生产环境中"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Neo4j 数据库设置
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    
    # SQLite 设置
    SQLITE_URL: str = os.getenv("SQLITE_URL", "sqlite:///./knowledge_graph.db")
    
    # 文件存储路径
    DOCUMENT_STORAGE_PATH: str = os.getenv("DOCUMENT_STORAGE_PATH", "./data/documents")
    WEB_ARCHIVE_PATH: str = os.getenv("WEB_ARCHIVE_PATH", "./data/web_archives")
    
    # SpaCy 模型设置
    SPACY_MODEL: str = os.getenv("SPACY_MODEL", "zh_core_web_sm")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()