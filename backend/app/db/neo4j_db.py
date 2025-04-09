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
        
        # 修正Cypher查询 - 使用正确的参数语法
        query = """
        CREATE (e:Entity)
        SET e = $props
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
    
    # 文件: backend/app/db/neo4j_db.py
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
        
        # 修正Cypher查询 - 使用正确的参数语法
        query = """
        MATCH (source)
        WHERE toString(source.id) = $source_id
        MATCH (target)
        WHERE toString(target.id) = $target_id
        CREATE (source)-[r:%s]->(target)
        SET r = $props
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
        try:
            # Convert the ID to string
            entity_id = str(id)
            print(f"Reading entity with ID: {entity_id}")
            
            # More flexible query that matches by string representation of ID
            query = """
            MATCH (e)
            WHERE toString(e.id) = $id
            RETURN e, labels(e) as labels
            """
            
            async with self.driver.session(database=self.database) as session:
                result = await session.run(query, id=entity_id)
                record = await result.single()
                
                if not record:
                    print(f"Entity not found with ID: {entity_id}")
                    return None
                    
                # Extract entity data
                entity_data = dict(record["e"])
                entity_labels = record["labels"]
                
                # Convert JSON strings back to Python objects
                for key, value in entity_data.items():
                    if isinstance(value, str) and key == "properties":
                        try:
                            entity_data[key] = json.loads(value)
                            print(f"Successfully parsed properties: {entity_data[key]}")
                        except json.JSONDecodeError as e:
                            print(f"Error parsing properties: {e}")
                            # Keep as string if can't parse
                
                # Determine entity type from labels
                entity_type = next((label for label in entity_labels if label != "Entity"), "Entity")
                entity_data["type"] = entity_type
                
                print(f"Found entity: {entity_data.get('name', 'Unnamed')} (Type: {entity_type})")
                
                # Return Entity object
                return Entity(**entity_data)
                    
        except Exception as e:
            print(f"Error in read method: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def update(self, id: UUID, obj: T) -> Optional[T]:
        """更新实体或关系"""
        try:
            # Ensure the ID is a string
            entity_id = str(id)
            print(f"Updating entity with ID: {entity_id}")
            
            # Get entity properties excluding certain fields
            entity_dict = obj.dict(exclude={"previous_version"})
            
            # 特别处理properties字段
            if "properties" in entity_dict:
                properties = entity_dict["properties"]
                print(f"Original properties: {properties}")
                
                # 确保properties是字典类型
                if not isinstance(properties, dict):
                    try:
                        # 如果是字符串，尝试解析为字典
                        if isinstance(properties, str):
                            properties = json.loads(properties)
                            print(f"Parsed properties from string: {properties}")
                        else:
                            properties = {}
                    except Exception as e:
                        print(f"Error parsing properties: {e}")
                        properties = {}
                
                # 更新properties字段
                entity_dict["properties"] = json.dumps(properties)
                print(f"Serialized properties to JSON: {entity_dict['properties']}")
            
            # Convert other complex types to JSON strings
            for key, value in entity_dict.items():
                if key != "properties" and isinstance(value, (dict, list)):
                    entity_dict[key] = json.dumps(value)
                elif isinstance(value, UUID):
                    entity_dict[key] = str(value)
            
            # Update node properties
            query = """
            MATCH (e)
            WHERE toString(e.id) = $id
            SET e = $properties
            """
            
            # Add or update entity type label
            type_query = """
            MATCH (e)
            WHERE toString(e.id) = $id
            WITH e, labels(e) as currentLabels
            CALL apoc.create.addLabels(e, [$type])
            YIELD node
            RETURN node
            """
            
            async with self.driver.session(database=self.database) as session:
                # Update properties
                await session.run(query, id=entity_id, properties=entity_dict)
                
                # Update type label
                if "type" in entity_dict and entity_dict["type"]:
                    try:
                        await session.run(type_query, id=entity_id, type=entity_dict["type"])
                    except Exception as type_error:
                        print(f"Error updating entity type: {type_error}")
                
                # Return the updated entity
                return obj
                    
        except Exception as e:
            print(f"Error in update method: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def delete(self, id: UUID) -> bool:
        """删除实体或关系"""
        try:
            # Convert the ID to string for query
            entity_id = str(id)
            print(f"Attempting to delete entity with ID: {entity_id}")
            
            # Use a more direct approach with explicit debugging
            query = """
            MATCH (e)
            WHERE e.id = $id
            WITH e, e.id as deleted_id
            DETACH DELETE e
            RETURN deleted_id
            """
            
            async with self.driver.session(database=self.database) as session:
                result = await session.run(query, id=entity_id)
                records = await result.data()
                
                success = len(records) > 0
                print(f"Delete operation result: {success}, Records: {records}")
                
                return success
        except Exception as e:
            print(f"Error in delete method: {e}")
            import traceback
            traceback.print_exc()
            return False
    
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
        
        try:
            async with self.driver.session(database=self.database) as session:
                # 首先更新属性
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
                
                result = await session.run(query, **params)
                record = await result.single()
                
                if not record:
                    print(f"Entity not found: {entity_id}")
                    return None
                    
                # 然后更新实体类型（标签）
                # 先获取当前的标签，除了"Entity"以外的
                labels_query = """
                MATCH (e:Entity {id: $id})
                RETURN labels(e) AS labels
                """
                
                labels_result = await session.run(labels_query, id=entity_id)
                labels_record = await labels_result.single()
                current_labels = labels_record["labels"]
                
                # 移除所有当前非Entity标签
                remove_labels_query = """
                MATCH (e:Entity {id: $id})
                """
                
                # 从当前标签中排除"Entity"和新类型
                labels_to_remove = [label for label in current_labels if label != "Entity" and label != entity.type]
                
                if labels_to_remove:
                    for label in labels_to_remove:
                        remove_label_query = f"""
                        MATCH (e:Entity {{id: $id}})
                        REMOVE e:{label}
                        """
                        await session.run(remove_label_query, id=entity_id)
                
                # 添加新标签
                add_label_query = f"""
                MATCH (e:Entity {{id: $id}})
                SET e:{entity.type}
                RETURN e
                """
                
                await session.run(add_label_query, id=entity_id)
                
                print(f"Successfully updated entity type to: {entity.type}")
                return entity
                
        except Exception as e:
            print(f"Error in _update_entity: {e}")
            raise e
    async def delete_relationship(self, id: UUID) -> bool:
        """删除关系"""
        try:
            # 确保ID是字符串
            rel_id = str(id)
            print(f"尝试删除关系，ID: {rel_id}")
            
            # 针对关系的特定查询
            query = """
            MATCH ()-[r]-()
            WHERE r.id = $id
            DELETE r
            RETURN count(r) as deleted_count
            """
            
            async with self.driver.session(database=self.database) as session:
                result = await session.run(query, id=rel_id)
                data = await result.data()
                
                # 检查是否有关系被删除
                if data and len(data) > 0:
                    deleted_count = data[0].get('deleted_count', 0)
                    success = deleted_count > 0
                else:
                    success = False
                
                print(f"关系删除操作结果: {success}, 记录: {data}")
                
                return success
        except Exception as e:
            print(f"删除关系方法出错: {e}")
            import traceback
            traceback.print_exc()
            return False