# 文件: app/core/config.py
import os
from typing import Any, Dict, Optional
from pydantic import validator, BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    # 基本配置
    PROJECT_NAME: str = "个人知识图谱系统"
    API_V1_PREFIX: str = "/api/v1"
    
    # 数据库配置
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    NEO4J_DATABASE: str = os.getenv("NEO4J_DATABASE", "neo4j")
      
    # 文件存储路径
    DOCUMENTS_DIR: str = os.getenv("DOCUMENTS_DIR", "./data/documents")
    ARCHIVES_DIR: str = os.getenv("ARCHIVES_DIR", "./data/archives")
    EXPORTS_DIR: str = os.getenv("EXPORTS_DIR", "./data/exports")
    
    # CORS配置
    CORS_ORIGINS: list = ["*"]
    
    # NLP配置
    SPACY_MODEL: str = os.getenv("SPACY_MODEL", "zh_core_web_sm")
    
    # 其他配置
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    @validator("DOCUMENTS_DIR", "ARCHIVES_DIR", "EXPORTS_DIR")
    def create_directories(cls, v):
        """确保目录存在"""
        os.makedirs(v, exist_ok=True)
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置对象
settings = Settings()