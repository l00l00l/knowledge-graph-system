# 文件: app/db/interfaces/database_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Generic, TypeVar, Type
from uuid import UUID

T = TypeVar('T')

class DatabaseInterface(Generic[T], ABC):
    """数据库操作接口基类"""
    
    @abstractmethod
    async def create(self, obj: T) -> T:
        """创建对象"""
        pass
    
    @abstractmethod
    async def read(self, id: UUID) -> Optional[T]:
        """读取对象"""
        pass
    
    @abstractmethod
    async def update(self, id: UUID, obj: T) -> Optional[T]:
        """更新对象"""
        pass
    
    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """删除对象"""
        pass
    
    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 100) -> List[T]:
        """列出对象"""
        pass
    
    @abstractmethod
    async def find(self, query: Dict[str, Any]) -> List[T]:
        """查找对象"""
        pass
