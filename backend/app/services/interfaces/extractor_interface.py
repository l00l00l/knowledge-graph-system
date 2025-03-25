# app/services/interfaces/extractor_interface.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

from app.models.entities.entity import Entity
from app.models.relationships.relationship import Relationship
from app.models.documents.source_document import SourceDocument


class KnowledgeExtractorInterface(ABC):
    """知识抽取接口基类，定义统一的知识抽取行为"""
    
    @abstractmethod
    async def extract_entities(self, document: SourceDocument, text_content: str) -> List[Entity]:
        """从文本中抽取实体"""
        pass
    
    @abstractmethod
    async def extract_relationships(self, document: SourceDocument, entities: List[Entity], text_content: str) -> List[Relationship]:
        """从文本中抽取实体间的关系"""
        pass
    
    @abstractmethod
    async def create_knowledge_traces(self, document: SourceDocument, entities: List[Entity], relationships: List[Relationship], text_content: str) -> bool:
        """创建知识溯源记录"""
        pass
    
    @abstractmethod
    async def detect_concepts(self, text_content: str) -> List[Dict[str, Any]]:
        """检测文本中的概念"""
        pass
    
    @abstractmethod
    async def map_to_ontology(self, entities: List[Entity]) -> Dict[str, Any]:
        """将实体映射到本体结构"""
        pass