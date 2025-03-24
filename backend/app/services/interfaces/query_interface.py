# 文件: app/services/interfaces/query_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from uuid import UUID
from app.models.entities.entity import Entity
from app.models.relationships.relationship import Relationship
from app.models.documents.source_document import SourceDocument
from app.models.documents.knowledge_trace import KnowledgeTrace


class QueryInterface(ABC):
    """查询接口基类"""
    
    @abstractmethod
    async def find_entities(self, query: Dict[str, Any]) -> List[Entity]:
        """查找实体"""
        pass
    
    @abstractmethod
    async def find_relationships(self, query: Dict[str, Any]) -> List[Relationship]:
        """查找关系"""
        pass
    
    @abstractmethod
    async def get_entity_context(self, entity_id: UUID) -> List[Dict[str, Any]]:
        """获取实体的上下文信息"""
        pass
    
    @abstractmethod
    async def trace_knowledge(self, entity_id: Optional[UUID] = None, relationship_id: Optional[UUID] = None) -> List[KnowledgeTrace]:
        """追溯知识来源"""
        pass
    
    @abstractmethod
    async def query_by_natural_language(self, query: str) -> Dict[str, Any]:
        """自然语言查询"""
        pass