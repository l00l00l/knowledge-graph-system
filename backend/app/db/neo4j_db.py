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
        """初始化Neo4j数据库连接"""
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.driver = AsyncGraphDatabase.driver(
            uri, 
            auth=(user, password),
            max_connection_lifetime=3600
        )
        print(f"Initialized Neo4j connection to {uri} with user {user} and database {database}")
    
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
        
        # 构建Cypher查询 - 修复实体创建查询
        query = """
        CREATE (e:Entity {props}) 
        SET e:%s 
        RETURN e
        """ % entity.type
        
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(query, props=props)
                record = await result.single()
                if record:
                    print(f"Successfully created entity: {entity.name}")
                else:
                    print(f"Warning: No record returned when creating entity: {entity.name}")
                return entity
        except Exception as e:
            print(f"Error in _create_entity: {e}")
            raise e
    
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
        
        # 构建Cypher查询 - 修复关系创建查询
        query = """
        MATCH (source:Entity {id: $source_id})
        MATCH (target:Entity {id: $target_id})
        CREATE (source)-[r:%s $props]->(target)
        RETURN r
        """ % relationship.type
        
        params = {
            "source_id": str(relationship.source_id),
            "target_id": str(relationship.target_id),
            "props": props
        }
        
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(query, **params)
                record = await result.single()
                if record:
                    print(f"Successfully created relationship of type {relationship.type}")
                else:
                    print(f"Warning: No record returned when creating relationship of type {relationship.type}")
                return relationship
        except Exception as e:
            print(f"Error in _create_relationship: {e}")
            raise e
    async def read(self, id: UUID) -> Optional[T]:
        """读取实体或关系"""
        # 这里需要实现具体的读取逻辑
        pass
    
    async def update(self, id: UUID, obj: T) -> Optional[T]:
        """更新实体或关系"""
        if isinstance(obj, Entity):
            return await self._update_entity(obj)
        elif isinstance(obj, Relationship):
            return await self._update_relationship(obj)
        else:
            raise TypeError(f"不支持的类型: {type(obj)}")
    
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

    async def test_connection(self) -> bool:
        """测试Neo4j连接"""
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run("RETURN 1 AS test")
                record = await result.single()
                return record and record["test"] == 1
        except Exception as e:
            print(f"Neo4j connection test failed: {e}")
            return False
        
    async def _update_entity(self, entity: Entity) -> Entity:
        """更新实体节点"""
        # 将Pydantic模型转为字典
        entity_dict = entity.dict()
        entity_id = str(entity.id)
        
        # 只更新特定属性，而不是替换整个节点
        props = {k: v for k, v in entity_dict.items() if v is not None and k not in ['id', 'type']}
        
        # 将复杂类型转换为JSON字符串
        for k, v in props.items():
            if isinstance(v, (dict, list)):
                props[k] = json.dumps(v)
            # 添加UUID转换
            elif isinstance(v, UUID):
                props[k] = str(v)
        
        # 构建Cypher查询 - 修改为更精确的更新
        query = """
        MATCH (e:Entity {id: $id})
        SET e.name = $name,
            e.description = $description,
            e.properties = $properties
        RETURN e
        """
        
        params = {
            "id": entity_id,
            "name": entity.name,
            "description": entity.description,
            "properties": json.dumps(entity.properties)
        }
        
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(query, **params)
                record = await result.single()
                
                # 如果需要更新标签（即实体类型发生变化）
                type_query = """
                MATCH (e:Entity {id: $id})
                CALL apoc.cypher.run("MATCH (e:Entity {id: $_id}) 
                                    REMOVE e:" + $old_labels + " 
                                    SET e:" + $new_label, 
                                    {_id: $id, old_labels: $old_labels, new_label: $new_label})
                YIELD value
                RETURN e
                """
                
                # 假设我们已经知道所有可能的类型
                types = ["person", "organization", "location", "concept", "time", "event"]
                old_labels = ":".join([t for t in types if t != entity.type])
                
                type_params = {
                    "id": entity_id,
                    "old_labels": old_labels,
                    "new_label": entity.type
                }
                
                # 执行类型更新
                await session.run(type_query, **type_params)
                
                if record:
                    print(f"Successfully updated entity: {entity.name}")
                    return entity
                else:
                    print(f"Entity not found: {entity_id}")
                    return None
        except Exception as e:
            print(f"Error in _update_entity: {e}")
            raise e