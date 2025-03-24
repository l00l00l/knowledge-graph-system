# 文件: app/models/relationships/relationship.py
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.core.base_model import TimeStampMixin, VersionMixin, SourceMixin


class Relationship(TimeStampMixin, VersionMixin, SourceMixin):
    """关系类，表示知识图谱中的边"""
    id: UUID = Field(default_factory=uuid4)
    type: str = Field(..., description="关系类型")
    source_id: UUID = Field(..., description="源实体ID")
    target_id: UUID = Field(..., description="目标实体ID")
    properties: Dict[str, Any] = Field(default_factory=dict, description="关系属性")
    bidirectional: bool = Field(default=False, description="是否为双向关系")
    start_time: Optional[datetime] = Field(default=None, description="关系开始时间")
    end_time: Optional[datetime] = Field(default=None, description="关系结束时间")
    certainty: float = Field(default=1.0, description="关系确定性(0-1)")
    evidence: Optional[str] = Field(default=None, description="支持该关系的证据")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "d2bed6a4-7ce6-4aa3-b011-89a86e099933",
                "type": "is_a",
                "source_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "target_id": "c21b28c3-dfcb-4c5a-89e4-75c1a28f5c64",
                "properties": {"context": "知识工程领域"},
                "bidirectional": False,
                "start_time": "2020-01-01T00:00:00Z",
                "end_time": None,
                "certainty": 0.95,
                "evidence": "根据多篇学术论文定义",
                "source_id": "e37f0136-7dc8-4dc9-92d7-b40b98e1a63d",
                "source_type": "document",
                "source_location": {"page": 7, "paragraph": 3, "char_offset": 210, "char_length": 30},
                "extraction_method": "rule_based",
                "confidence": 0.85,
                "created_at": "2023-01-15T09:35:00Z",
                "updated_at": "2023-01-15T09:35:00Z",
                "version": 1,
                "previous_version": None
            }
        }
