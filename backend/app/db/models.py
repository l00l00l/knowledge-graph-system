from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
import datetime
import json
from .sqlite_db import Base


class EntityType(Base):
    """实体类型定义"""
    __tablename__ = "entity_types"
    
    id = Column(Integer, primary_key=True)
    type_code = Column(String, unique=True, index=True)  # 类型编码，如 'person'
    type_name = Column(String)  # 类型中文名称，如 '人物'
    category = Column(String, index=True)  # 类别：基础类型、领域类型、个人类型
    icon = Column(String, nullable=True)  # 图标类，如 'fa-user'
    color = Column(String, nullable=True)  # 颜色代码，如 '#ff7f0e'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class RelationshipType(Base):
    """关系类型定义"""
    __tablename__ = "relationship_types"
    
    id = Column(Integer, primary_key=True)
    type_code = Column(String, unique=True, index=True)  # 类型编码，如 'is_a'
    type_name = Column(String)  # 类型中文名称，如 '是一种'
    category = Column(String, index=True)  # 类别：基础类型、领域类型、个人类型
    icon = Column(String, nullable=True)  # 图标类，如 'fa-sitemap'
    color = Column(String, nullable=True)  # 颜色代码，如 '#999999'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
class Document(Base):
    """文档模型"""
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, index=True)
    type = Column(String, index=True)
    content_hash = Column(String)
    file_path = Column(String)
    url = Column(String, nullable=True)
    archived_path = Column(String, nullable=True)
    doc_metadata = Column(Text, nullable=True)  # 重命名为doc_metadata
    accessed_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def to_dict(self):
        """转换为字典，方便API返回"""
        try:
            # Parse doc_metadata from JSON string if it exists
            metadata = {}
            if self.doc_metadata:
                try:
                    # Print the raw value for debugging
                    print(f"Raw doc_metadata for {self.id}: {self.doc_metadata[:100]}...")
                    metadata = json.loads(self.doc_metadata)
                except Exception as e:
                    print(f"Warning: Failed to parse doc_metadata for document {self.id}: {e}")
                    # Try to handle it as a string directly
                    metadata = {"raw": self.doc_metadata}
            
            return {
                "id": self.id,
                "title": self.title,
                "type": self.type,
                "content_hash": self.content_hash,
                "file_path": self.file_path,
                "url": self.url,
                "archived_path": self.archived_path,
                "metadata": metadata,  # Now with better fallback
                "accessed_at": self.accessed_at.isoformat() if self.accessed_at else None,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None
            }
        except Exception as e:
            print(f"Error in to_dict for document {self.id}: {e}")
            # Return minimal data to avoid complete failure
            return {
                "id": self.id,
                "title": self.title or "Unknown",
                "type": self.type or "unknown",
                "error": "Error converting document data"
            }