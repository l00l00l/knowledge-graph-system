# 文件: app/models/documents/knowledge_trace.py
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from app.models.core.base_model import TimeStampMixin


class KnowledgeTrace(TimeStampMixin):
    """知识溯源类，连接知识点与源数据"""
    id: UUID = Field(default_factory=uuid4)
    entity_id: Optional[UUID] = Field(default=None, description="相关实体ID")
    relationship_id: Optional[UUID] = Field(default=None, description="相关关系ID")
    document_id: UUID = Field(..., description="源文档ID")
    location_data: Dict[str, Any] = Field(..., description="定位数据")
    context_range: Dict[str, Any] = Field(default_factory=dict, description="上下文范围")
    excerpt: Optional[str] = Field(default=None, description="原文摘录")
    anchor_type: str = Field(default="char_offset", description="锚点类型: char_offset, xpath, semantic")
    anchor_data: Dict[str, Any] = Field(..., description="锚点详细数据")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-4a5b-9c3d-2e1f0a9b8c7d",
                "entity_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "relationship_id": None,
                "document_id": "e37f0136-7dc8-4dc9-92d7-b40b98e1a63d",
                "location_data": {
                    "page": 5,
                    "paragraph": 2,
                    "char_offset": 120,
                    "char_length": 45
                },
                "context_range": {
                    "before_chars": 100,
                    "after_chars": 100
                },
                "excerpt": "知识图谱是一种表示知识的图结构，由节点和边组成，节点表示实体，边表示实体间的关系。",
                "anchor_type": "char_offset",
                "anchor_data": {
                    "start_offset": 120,
                    "end_offset": 165,
                    "content_fingerprint": "哈希值用于确认内容匹配"
                },
                "created_at": "2023-01-15T09:40:00Z",
                "updated_at": "2023-01-15T09:40:00Z"
            }
        }