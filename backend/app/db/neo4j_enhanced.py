# app/db/neo4j_enhanced.py

from typing import Dict, Any, List, Optional, Union, TypeVar, Generic
from uuid import UUID
import json
import asyncio
from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.exceptions import Neo4jError

from app.db.interfaces.database_interface import DatabaseInterface
from app.models.core.base_model import BaseModel
from app.core.exceptions import DatabaseError
from app.core.logger import logger

T = TypeVar('T', bound=BaseModel)

class Neo4jEnhanced(DatabaseInterface, Generic[T]):
    """增强版Neo4j数据库接口，提供高级查询与版本管理功能"""
    
    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.driver: Optional[AsyncDriver] = None
        self._init_driver()
        
    def _init_driver(self):
        """初始化数据库驱动"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri, 
                auth=(self.user, self.password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60
            )
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j driver: {e}")
            raise DatabaseError(f"Database connection error: {e}")
    
    async def close(self):
        """关闭数据库连接"""
        if self.driver:
            await self.driver.close()
    
    async def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """执行通用Cypher查询"""
        if not self.driver:
            self._init_driver()
            
        params = params or {}
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(query, **params)
                records = await result.values()
                return [self._process_record(record) for record in records]
        except Neo4jError as e:
            logger.error(f"Neo4j query error: {e}")
            raise DatabaseError(f"Query execution failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during query execution: {e}")
            raise DatabaseError(f"Unexpected error: {e}")
    
    async def execute_read_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """执行只读查询，使用读取事务"""
        if not self.driver:
            self._init_driver()
            
        params = params or {}
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.execute_read(
                    lambda tx: tx.run(query, **params)
                )
                records = await result.values()
                return [self._process_record(record) for record in records]
        except Neo4jError as e:
            logger.error(f"Neo4j read query error: {e}")
            raise DatabaseError(f"Read query execution failed: {e}")
    
    async def execute_write_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """执行写入查询，使用写入事务"""
        if not self.driver:
            self._init_driver()
            
        params = params or {}
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.execute_write(
                    lambda tx: tx.run(query, **params)
                )
                records = await result.values()
                return [self._process_record(record) for record in records]
        except Neo4jError as e:
            logger.error(f"Neo4j write query error: {e}")
            raise DatabaseError(f"Write query execution failed: {e}")
    
    def _process_record(self, record: Any) -> Dict[str, Any]:
        """处理查询结果记录，转换为字典格式"""
        if isinstance(record, (list, tuple)):
            return [self._convert_neo4j_types(item) for item in record]
        else:
            return self._convert_neo4j_types(record)
    
    def _convert_neo4j_types(self, value: Any) -> Any:
        """递归转换Neo4j类型为Python标准类型"""
        # 处理Neo4j节点
        if hasattr(value, 'id') and hasattr(value, 'labels'):
            result = dict(value.items())
            result['_id'] = value.id
            result['_labels'] = list(value.labels)
            return result
        # 处理Neo4j关系
        elif hasattr(value, 'id') and hasattr(value, 'type'):
            result = dict(value.items())
            result['_id'] = value.id
            result['_type'] = value.type
            result['_start_node'] = value.start_node.id
            result['_end_node'] = value.end_node.id
            return result
        # 处理列表和字典
        elif isinstance(value, list):
            return [self._convert_neo4j_types(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._convert_neo4j_types(v) for k, v in value.items()}
        # 返回原始值
        return value
    
    # 实现DatabaseInterface的方法
    async def create(self, obj: T) -> T:
        """创建实体或关系"""
        # 实现逻辑...
        pass
        
    async def read(self, id: UUID) -> Optional[T]:
        """读取实体或关系"""
        # 实现逻辑...
        pass
        
    async def update(self, id: UUID, obj: T) -> Optional[T]:
        """更新实体或关系"""
        # 实现逻辑...
        pass
        
    async def delete(self, id: UUID) -> bool:
        """删除实体或关系"""
        # 实现逻辑...
        pass
        
    async def list(self, skip: int = 0, limit: int = 100) -> List[T]:
        """列出实体或关系"""
        # 实现逻辑...
        pass
        
    async def find(self, query: Dict[str, Any]) -> List[T]:
        """查找实体或关系"""
        # 实现逻辑...
        pass