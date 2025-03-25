# app/services/interfaces/provenance_interface.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from uuid import UUID

from app.models.documents.knowledge_trace import KnowledgeTrace


class ProvenanceInterface(ABC):
    """知识溯源接口基类，定义统一的溯源行为"""
    
    @abstractmethod
    async def create_trace(self, entity_id: Optional[UUID], relationship_id: Optional[UUID], 
                          document_id: UUID, location_data: Dict[str, Any],
                          excerpt: str) -> KnowledgeTrace:
        """创建溯源记录"""
        pass
    
    @abstractmethod
    async def find_traces(self, entity_id: Optional[UUID] = None, 
                         relationship_id: Optional[UUID] = None,
                         document_id: Optional[UUID] = None) -> List[KnowledgeTrace]:
        """查找溯源记录"""
        pass
    
    @abstractmethod
    async def get_original_context(self, trace_id: UUID) -> Dict[str, Any]:
        """获取原始上下文"""
        pass
    
    @abstractmethod
    async def update_trace(self, trace_id: UUID, data: Dict[str, Any]) -> KnowledgeTrace:
        """更新溯源记录"""
        pass
    
    @abstractmethod
    async def delete_trace(self, trace_id: UUID) -> bool:
        """删除溯源记录"""
        pass