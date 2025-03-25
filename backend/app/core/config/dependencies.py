# app/core/dependencies.py

from typing import Generator
from fastapi import Depends

from app.db.neo4j_db import Neo4jDatabase
from app.services.document_processor import DocumentProcessor
from app.services.knowledge_extractor import KnowledgeExtractor
from app.services.query_service import QueryService
from app.services.provenance_service import ProvenanceService
from app.services.nlp_service import NLPService
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


async def get_document_processor(db: Neo4jDatabase = Depends(get_db)) -> DocumentProcessor:
    """获取文档处理器实例"""
    return DocumentProcessor(
        documents_dir=settings.DOCUMENTS_DIR,
        archives_dir=settings.ARCHIVES_DIR
    )


async def get_knowledge_extractor(db: Neo4jDatabase = Depends(get_db)) -> KnowledgeExtractor:
    """获取知识抽取器实例"""
    return KnowledgeExtractor(db, model_name=settings.SPACY_MODEL)


async def get_query_service(db: Neo4jDatabase = Depends(get_db)) -> QueryService:
    """获取查询服务实例"""
    return QueryService(db)


async def get_provenance_service(db: Neo4jDatabase = Depends(get_db)) -> ProvenanceService:
    """获取溯源服务实例"""
    return ProvenanceService(db)


async def get_nlp_service() -> NLPService:
    """获取NLP服务实例"""
    return NLPService(model_name=settings.SPACY_MODEL)