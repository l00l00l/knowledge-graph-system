# 文件: app/models/core/base_model.py
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class TimeStampMixin(BaseModel):
    """时间戳混入类，提供创建和更新时间追踪"""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class VersionMixin(BaseModel):
    """版本控制混入类，提供版本追踪功能"""
    version: int = Field(default=1)
    previous_version: Optional[UUID] = Field(default=None)
    

class SourceMixin(BaseModel):
    """溯源混入类，提供知识溯源能力"""
    source_id: Optional[UUID] = Field(default=None, description="源数据ID")
    source_type: Optional[str] = Field(default=None, description="源数据类型: document, webpage, structured_data")
    source_location: Optional[Dict[str, Any]] = Field(default=None, description="源数据中的位置信息")
    extraction_method: Optional[str] = Field(default=None, description="知识抽取方法")
    confidence: Optional[float] = Field(default=None, description="抽取置信度")