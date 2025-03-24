# 文件: app/models/documents/source_document.py
from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.core.base_model import TimeStampMixin


class SourceDocument(TimeStampMixin):
    """源文档类，表示知识的原始来源"""
    id: UUID = Field(default_factory=uuid4)
    title: str = Field(..., description="文档标题")
    type: str = Field(..., description="文档类型: pdf, docx, txt, webpage, csv, json")
    content_hash: str = Field(..., description="内容哈希，用于唯一标识和检测变更")
    file_path: Optional[str] = Field(default=None, description="文件路径")
    url: Optional[str] = Field(default=None, description="原始URL")
    archived_path: Optional[str] = Field(default=None, description="归档路径")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="文档元数据")
    accessed_at: datetime = Field(default_factory=datetime.now, description="最后访问时间")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "e37f0136-7dc8-4dc9-92d7-b40b98e1a63d",
                "title": "知识图谱：机遇与挑战",
                "type": "pdf",
                "content_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "file_path": "/data/documents/KnowledgeGraphs.pdf",
                "url": "https://example.com/papers/knowledge_graphs.pdf",
                "archived_path": "/data/archives/e37f0136-7dc8-4dc9-92d7-b40b98e1a63d.pdf",
                "metadata": {
                    "author": "张三",
                    "publication_date": "2022-03-15",
                    "publisher": "数据科学出版社",
                    "pages": 36
                },
                "accessed_at": "2023-01-15T09:28:00Z",
                "created_at": "2023-01-15T09:28:00Z",
                "updated_at": "2023-01-15T09:28:00Z"
            }
        }
