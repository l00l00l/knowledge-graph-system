from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
import datetime
from .sqlite_db import Base

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
    metadata = Column(Text, nullable=True)  # 存储为JSON字符串
    accessed_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def to_dict(self):
        """转换为字典，方便API返回"""
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "content_hash": self.content_hash,
            "file_path": self.file_path,
            "url": self.url,
            "archived_path": self.archived_path,
            "metadata": self.metadata,
            "accessed_at": self.accessed_at.isoformat() if self.accessed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }