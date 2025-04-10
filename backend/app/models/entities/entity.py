# 文件: app/models/entities/entity.py
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from app.models.core.base_model import TimeStampMixin, VersionMixin, SourceMixin


class Entity(TimeStampMixin, VersionMixin, SourceMixin):
    """实体基类，表示知识图谱中的节点"""
    id: UUID = Field(default_factory=uuid4)
    type: str = Field(..., description="实体类型")
    name: str = Field(..., description="实体名称")
    description: Optional[str] = Field(default=None, description="实体描述")
    properties: Dict[str, Any] = Field(default_factory=dict, description="实体属性")
    tags: List[str] = Field(default_factory=list, description="实体标签")
    importance: Optional[int] = Field(default=None, description="实体重要度(1-5)")
    understanding_level: Optional[int] = Field(default=None, description="理解程度(1-5)")
    personal_notes: Optional[str] = Field(default=None, description="个人笔记")
    category: Optional[str] = Field(default=None, description="实体分类(基础类型、领域类型、个人类型)")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "type": "concept",
                "name": "知识图谱",
                "description": "一种表示知识的图结构",
                "properties": {"domain": "人工智能", "first_encountered": "2022-05-10"},
                "tags": ["知识表示", "图数据", "人工智能"],
                "importance": 5,
                "understanding_level": 4,
                "personal_notes": "这是我研究的核心概念",
                "source_id": "e37f0136-7dc8-4dc9-92d7-b40b98e1a63d",
                "source_type": "document",
                "source_location": {"page": 5, "paragraph": 2, "char_offset": 120, "char_length": 45},
                "extraction_method": "manual",
                "confidence": 1.0,
                "created_at": "2023-01-15T09:30:00Z",
                "updated_at": "2023-01-15T09:30:00Z",
                "version": 1,
                "previous_version": None
            }
        }

