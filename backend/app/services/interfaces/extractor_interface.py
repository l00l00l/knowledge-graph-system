# 文件: app/services/interfaces/extractor_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from app.models.entities.entity import Entity
from app.models.relationships.relationship import Relationship
from app.models.documents.source_document import SourceDocument


class ExtractorInterface(ABC):
    """知识抽取接口基类"""
    
    @abstractmethod
    async def extract_entities(self, document: SourceDocument) -> List[Entity]:
        """从源文档中抽取实体"""
        pass
    
    @abstractmethod
    async def extract_relationships(self, document: SourceDocument, entities: List[Entity]) -> List[Relationship]:
        """从源文档中抽取关系"""
        pass
    
    @abstractmethod
    async def create_knowledge_traces(self, document: SourceDocument, entities: List[Entity], relationships: List[Relationship]) -> bool:
        """创建知识溯源记录"""
        pass