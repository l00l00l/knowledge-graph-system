# app/services/interfaces/document_processor_interface.py

from abc import ABC, abstractmethod
from typing import Dict, Any, BinaryIO, Optional
from uuid import UUID

from app.models.documents.source_document import SourceDocument


class DocumentProcessorInterface(ABC):
    """文档处理接口基类，定义统一的文档处理行为"""
    
    @abstractmethod
    async def process_file(self, file: BinaryIO, filename: str) -> Dict[str, Any]:
        """处理上传文件"""
        pass
    
    @abstractmethod
    async def process_url(self, url: str) -> Dict[str, Any]:
        """处理网页URL"""
        pass
    
    @abstractmethod
    async def extract_content(self, document_id: UUID) -> str:
        """提取文档内容"""
        pass
    
    @abstractmethod
    async def get_document_metadata(self, document_id: UUID) -> Dict[str, Any]:
        """获取文档元数据"""
        pass
    
    @abstractmethod
    async def retrieve_original_context(self, document_id: UUID, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """检索原始上下文"""
        pass