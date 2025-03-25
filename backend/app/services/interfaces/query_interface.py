# app/services/interfaces/query_interface.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from uuid import UUID

from app.models.entities.entity import Entity
from app.models.relationships.relationship import Relationship


class QueryInterface(ABC):
    """查询接口基类，定义统一的查询行为"""
    
    @abstractmethod
    async def query_by_natural_language(self, query: str) -> Dict[str, Any]:
        """自然语言查询知识图谱"""
        pass
    
    @abstractmethod
    async def find_entities(self, query: Dict[str, Any]) -> List[Entity]:
        """条件查询实体"""
        pass
    
    @abstractmethod
    async def find_relationships(self, query: Dict[str, Any]) -> List[Relationship]:
        """条件查询关系"""
        pass
    
    @abstractmethod
    async def get_entity_context(self, entity_id: UUID) -> Dict[str, Any]:
        """获取实体上下文信息"""
        pass
    
    @abstractmethod
    async def suggest_related_knowledge(self, entity_ids: List[UUID]) -> Dict[str, Any]:
        """推荐相关知识"""
        pass