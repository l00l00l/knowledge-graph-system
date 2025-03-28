# 文件: app/db/neo4j_db.py
from typing import Dict, Any, Optional, List, Generic, TypeVar, Type
from uuid import UUID
import json
from neo4j import AsyncGraphDatabase
from app.db.interfaces.database_interface import DatabaseInterface
from app.models.entities.entity import Entity
from app.models.relationships.relationship import Relationship

T = TypeVar('T', Entity, Relationship)

class Neo4jDatabase(DatabaseInterface[T]):
    """Neo4j图数据库实现"""
    
    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        self.database = database
    
    async def close(self):
        await self.driver.close()
    
    async def create(self, obj: T) -> T:
        """创建实体或关系"""
        if isinstance(obj, Entity):
            return await self._create_entity(obj)
        elif isinstance(obj, Relationship):
            return await self._create_relationship(obj)
        else:
            raise TypeError(f"不支持的类型: {type(obj)}")
    
    async def _create_entity(self, entity: Entity) -> Entity:
        """创建实体节点"""
        # 将Pydantic模型转为字典，避免非Neo4j支持的类型
        entity_dict = entity.dict()
        props = {k: v for k, v in entity_dict.items() if v is not None and k != 'type'}
        
        # 将复杂类型转换为JSON字符串
        for k, v in props.items():
            if isinstance(v, (dict, list)):
                props[k] = json.dumps(v)
            # 添加UUID转换
            elif isinstance(v, UUID):
                props[k] = str(v)
        
        # 构建Cypher查询
        query = """
        CREATE (e:`Entity`:`%s` $props) 
        RETURN e
        """ % entity.type
        
        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, props=props)
            record = await result.single()
            return entity
    
    async def _create_relationship(self, relationship: Relationship) -> Relationship:
        """创建关系边"""
        # 将Pydantic模型转为字典
        rel_dict = relationship.dict()
        props = {k: v for k, v in rel_dict.items() 
                if v is not None and k not in ('type', 'source_id', 'target_id')}
        
        # 将复杂类型转换为JSON字符串
        for k, v in props.items():
            if isinstance(v, (dict, list)):
                props[k] = json.dumps(v)
            # 添加UUID转换
            elif isinstance(v, UUID):
                props[k] = str(v)
        
        # 构建Cypher查询
        query = """
        MATCH (source:Entity {id: $source_id})
        MATCH (target:Entity {id: $target_id})
        CREATE (source)-[r:`%s` $props]->(target)
        RETURN r
        """ % relationship.type
        
        params = {
            "source_id": str(relationship.source_id),
            "target_id": str(relationship.target_id),
            "props": props
        }
        
        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, **params)
            record = await result.single()
            return relationship
    
    async def read(self, id: UUID) -> Optional[T]:
        """读取实体或关系"""
        # 这里需要实现具体的读取逻辑
        pass
    
    async def update(self, id: UUID, obj: T) -> Optional[T]:
        """更新实体或关系"""
        # 这里需要实现具体的更新逻辑
        pass
    
    async def delete(self, id: UUID) -> bool:
        """删除实体或关系"""
        # 这里需要实现具体的删除逻辑
        pass
    
    async def list(self, skip: int = 0, limit: int = 100) -> List[T]:
        """列出实体或关系"""
        # 这里需要实现具体的列表逻辑
        pass
    
    async def find(self, query: Dict[str, Any]) -> List[T]:
        """查找实体或关系"""
        # 这里需要实现具体的查找逻辑
        pass
