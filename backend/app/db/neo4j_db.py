# 文件: app/db/neo4j_db.py
from datetime import datetime  # 直接导入类
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
        #props = {k: v for k, v in entity_dict.items() if v is not None and k != 'type'}
        props = {k: v for k, v in entity_dict.items() if v is not None}

        # 明确设置时间戳为ISO格式字符串
        from datetime import datetime
        current_time = datetime.now().isoformat()
        
        props['created_at'] = current_time
        props['updated_at'] = current_time
        
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
        
        # 提取关键信息，确保source_id和target_id正确设置
        source_id = rel_dict.get("source_id")
        target_id = rel_dict.get("target_id")
        
        if not source_id or not target_id:
            raise ValueError("Relationship must have both source_id and target_id")
        
        # 准备关系属性，排除特定字段
        props = {k: v for k, v in rel_dict.items() 
                if v is not None and k not in ('type', 'source_id', 'target_id')}
        
        # 将复杂类型转换为JSON字符串
        for k, v in props.items():
            if isinstance(v, (dict, list)):
                props[k] = json.dumps(v)
            # 添加UUID转换
            elif isinstance(v, UUID):
                props[k] = str(v)
            # 添加datetime转换
            elif k in ["created_at", "updated_at"] and hasattr(v, "isoformat"):
                props[k] = v.isoformat()
        
        # 确保created_at和updated_at字段存在
        from datetime import datetime
        now_str = datetime.now().isoformat()
        if "created_at" not in props:
            props["created_at"] = now_str
        if "updated_at" not in props:
            props["updated_at"] = now_str
        
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
            "source_id": str(source_id),
            "target_id": str(target_id),
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
        
    async def read_relationship(self, id: UUID) -> Optional[Relationship]:
        """读取关系"""
        try:
            rel_id = str(id)
            print(f"Reading relationship with ID: {rel_id}")
            
            query = """
            MATCH ()-[r]-()
            WHERE r.id.id = $id
            RETURN r, startNode(r) as source, endNode(r) as target
            """
            
            async with self.driver.session(database=self.database) as session:
                result = await session.run(query, id=rel_id)
                record = await result.single()
                
                if not record:
                    print(f"Relationship not found with ID: {rel_id}")
                    return None
                    
                # 提取关系数据
                rel_data = dict(record["r"])
                source_node = record["source"]
                target_node = record["target"]
                
                # 添加源和目标ID
                rel_data["source_id"] = source_node.get("id")
                rel_data["target_id"] = target_node.get("id")
                
                # 处理特殊字段
                for key, value in list(rel_data.items()):
                    if isinstance(value, str) and key == "properties":
                        try:
                            rel_data[key] = json.loads(value)
                        except:
                            rel_data[key] = {}
                
                # 返回关系对象
                return Relationship(**rel_data)
        except Exception as e:
            print(f"Error reading relationship: {e}")
            return None
    async def read(self, id: UUID) -> Optional[T]:
        """读取实体或关系"""
        try:
            # 确保ID是字符串
            entity_id = str(id)
            print(f"Reading entity with ID: {entity_id}")
            
            # 使用更灵活的查询语句，通过ID字符串表示匹配
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
                    
                # 提取实体数据
                entity_data = dict(record["e"])
                entity_labels = record["labels"]

                from datetime import datetime
                current_time = datetime.now()
                # 确保时间戳字段存在且类型正确
                if 'created_at' not in entity_data or entity_data['created_at'] is None:
                    entity_data['created_at'] = current_time
                
                if 'updated_at' not in entity_data or entity_data['updated_at'] is None:
                    entity_data['updated_at'] = current_time
                # 处理时间字段 - 强制转换为字符串
                if 'created_at' in entity_data:
                    try:
                        # 无论原始类型是什么，强制转换为字符串
                        entity_data['created_at'] = str(entity_data['created_at'])
                    except:
                        entity_data['created_at'] = datetime.now().isoformat()
                else:
                    entity_data['created_at'] = datetime.now().isoformat()
                if 'updated_at' in entity_data:
                    try:
                        entity_data['updated_at'] = str(entity_data['updated_at'])
                    except:
                        entity_data['updated_at'] = datetime.now().isoformat()
                else:
                    entity_data['updated_at'] = datetime.now().isoformat()

                # 特别处理source_location字段
                if 'source_location' in entity_data:
                    if entity_data['source_location'] is None:
                        entity_data['source_location'] = {}
                    elif isinstance(entity_data['source_location'], str):
                        try:
                            entity_data['source_location'] = json.loads(entity_data['source_location'])
                        except:
                            entity_data['source_location'] = {}
                    elif not isinstance(entity_data['source_location'], dict):
                        entity_data['source_location'] = {}
                
                # 处理JSON字符串字段
                for key, value in list(entity_data.items()):
                    if isinstance(value, str):
                        if key == "properties":
                            try:
                                entity_data[key] = json.loads(value)
                                print(f"Successfully parsed properties: {entity_data[key]}")
                            except json.JSONDecodeError as e:
                                print(f"Error parsing properties: {e}")
                                # 如果解析失败，保持原样
                        elif key == "tags":
                            try:
                                entity_data[key] = json.loads(value)
                                print(f"Successfully parsed tags: {entity_data[key]}")
                            except json.JSONDecodeError as e:
                                print(f"Error parsing tags: {e}")
                                # 如果解析失败，设置为空列表
                                entity_data[key] = []
                
                # 确保tags字段是列表
                if "tags" not in entity_data or entity_data["tags"] is None:
                    entity_data["tags"] = []
                elif not isinstance(entity_data["tags"], list):
                    entity_data["tags"] = []
                    print(f"Corrected tags field to empty list")
                
                # 确定实体类型
                entity_type = next((label for label in entity_labels if label != "Entity"), "Entity")
                entity_data["type"] = entity_type
                
                print(f"Found entity: {entity_data.get('name', 'Unnamed')} (Type: {entity_type})")
                
                # 返回实体对象
                # 尝试创建实体对象，添加更详细的错误处理
                try:
                    return Entity(**entity_data)
                except Exception as validation_error:
                    print(f"严重：实体验证错误 {validation_error}，尝试修复...")
                    
                    # 修复所有可能的问题
                    for field in ['source_id', 'source_type', 'extraction_method']:
                        if field in entity_data and not isinstance(entity_data[field], (str, type(None))):
                            entity_data[field] = None
                    
                    for field in ['confidence', 'importance', 'understanding_level']:
                        if field in entity_data and not isinstance(entity_data[field], (float, int, type(None))):
                            entity_data[field] = None
                    
                    # 最后一次尝试创建实体
                    try:
                        return Entity(**entity_data)
                    except Exception as final_error:
                        print(f"无法修复实体验证错误，最终错误: {final_error}")
                        return None
                    
        except Exception as e:
            print(f"Error in read method: {e}")
            import traceback
            traceback.print_exc()
            return None
    async def update(self, id: UUID, obj: T) -> Optional[T]:
        # 这段代码会添加到现有的 update 方法中，确保它能处理 Relationship 类型的对象
        if isinstance(obj, Relationship):
            # 获取关系ID，确保是字符串
            rel_id = str(id)
            print(f"Updating relationship with ID: {rel_id}")
            
            # 获取关系属性
            rel_dict = obj.dict(exclude={"previous_version"})
            
            # 处理特殊字段
            for key, value in list(rel_dict.items()):
                if isinstance(value, (dict, list)):
                    rel_dict[key] = json.dumps(value)
                elif isinstance(value, UUID):
                    rel_dict[key] = str(value)
                elif key in ["created_at", "updated_at"] and hasattr(value, "isoformat"):
                    rel_dict[key] = value.isoformat()
            
            # 设置更新时间
            rel_dict["updated_at"] = datetime.now().isoformat()
            
            # 构建动态SET语句
            set_statements = []
            params = {"id": rel_id}
            
            for key, value in rel_dict.items():
                if key not in ["id", "source_id", "target_id", "type"]:  # 跳过这些字段
                    set_statements.append(f"r.{key} = ${key}")
                    params[key] = value
            
            # 如果没有可更新的属性，直接返回原始对象
            if not set_statements:
                return obj
            
            # 构建Cypher查询
            query = f"""
            MATCH ()-[r]-()
            WHERE r.id = $id
            SET {", ".join(set_statements)}
            RETURN r
            """
            
            try:
                async with self.driver.session(database=self.database) as session:
                    result = await session.run(query, **params)
                    record = await result.single()
                    
                    if record:
                        print(f"Successfully updated relationship properties")
                        return obj
                    else:
                        print(f"Warning: No record returned when updating relationship")
                        return None
            except Exception as e:
                print(f"Error updating relationship: {e}")
                return None
        """更新实体或关系"""
        try:
            # 确保ID是字符串
            entity_id = str(id)
            print(f"Updating entity with ID: {entity_id}")
            
            # 获取实体属性（排除某些内部字段）
            entity_dict = obj.dict(exclude={"previous_version"})
            
            # 处理特殊字段（如properties, tags等）
            for key, value in list(entity_dict.items()):
                # 如果是字典或列表类型，转换为JSON字符串
                if isinstance(value, (dict, list)):
                    entity_dict[key] = json.dumps(value)
                # 如果是UUID类型，转换为字符串
                elif isinstance(value, UUID):
                    entity_dict[key] = str(value)
                # 如果是datetime类型，转换为ISO格式字符串
                elif key in ["created_at", "updated_at"] and hasattr(value, "isoformat"):
                    entity_dict[key] = value.isoformat()
            
            # 设置更新时间
            entity_dict["updated_at"] = datetime.now().isoformat()
            
            # 构建动态SET语句
            set_statements = []
            params = {"id": entity_id}
            
            for key, value in entity_dict.items():
                if key != "id":  # 跳过ID字段
                    set_statements.append(f"e.{key} = ${key}")
                    params[key] = value
            
            # 如果没有可更新的属性，直接返回原始对象
            if not set_statements:
                return obj
            
            # 构建Cypher查询
            query = f"""
            MATCH (e)
            WHERE toString(e.id) = $id
            SET {", ".join(set_statements)}
            RETURN e
            """
            
            async with self.driver.session(database=self.database) as session:
                # 执行属性更新
                result = await session.run(query, **params)
                record = await result.single()
                
                if record:
                    print(f"Successfully updated entity properties")
                else:
                    print(f"Warning: No record returned when updating entity properties")
                
                # 如果更新包含类型变更，更新节点标签
                if "type" in entity_dict and entity_dict["type"]:
                    type_value = entity_dict["type"]
                    
                    try:
                        # 首先获取当前节点的所有标签
                        labels_query = """
                        MATCH (e)
                        WHERE toString(e.id) = $id
                        RETURN labels(e) AS labels
                        """
                        
                        labels_result = await session.run(labels_query, id=entity_id)
                        labels_record = await labels_result.single()
                        
                        if labels_record:
                            current_labels = labels_record["labels"]
                            
                            # 移除除"Entity"和新类型外的所有标签
                            for label in current_labels:
                                if label != "Entity" and label != type_value:
                                    remove_query = f"""
                                    MATCH (e)
                                    WHERE toString(e.id) = $id
                                    REMOVE e:{label}
                                    """
                                    await session.run(remove_query, id=entity_id)
                                    print(f"Removed old type label: {label}")
                        
                        # 添加新类型标签
                        add_label_query = f"""
                        MATCH (e)
                        WHERE toString(e.id) = $id
                        SET e:{type_value}
                        RETURN e
                        """
                        
                        await session.run(add_label_query, id=entity_id)
                        print(f"Added new type label: {type_value}")
                    except Exception as type_error:
                        print(f"Error updating entity type: {type_error}")
            
            # 直接返回原始对象
            return obj
                
        except Exception as e:
            print(f"Error in update method: {e}")
            import traceback
            traceback.print_exc()
            return None
    async def update_bak(self, id: UUID, obj: T) -> Optional[T]:
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
                print(f"Original properties before processing: {properties}")
                
                # 确保properties是字典类型
                if not isinstance(properties, dict):
                    try:
                        # 如果是字符串，尝试解析为字典
                        if isinstance(properties, str):
                            properties = json.loads(properties)
                            print(f"Parsed properties from string: {properties}")
                        else:
                            # 如果不是字典也不是字符串，使用空字典
                            properties = {}
                            print("Properties is neither dict nor string, using empty dict")
                    except Exception as e:
                        print(f"Error parsing properties: {e}")
                        properties = {}
                
                # 确保所有属性值都是可序列化的
                clean_props = {}
                for k, v in properties.items():
                    if isinstance(v, (dict, list)):
                        clean_props[k] = json.dumps(v)
                    elif isinstance(v, UUID):
                        clean_props[k] = str(v)
                    else:
                        clean_props[k] = v
                
                # 用处理后的properties替换原始properties
                entity_dict["properties"] = json.dumps(clean_props)
                #print(f"Properties serialized to JSON: {entity_dict['properties']}")
            
            # 特别处理tags字段，确保它是JSON字符串
            if "tags" in entity_dict:
                if isinstance(entity_dict["tags"], list):
                    entity_dict["tags"] = json.dumps(entity_dict["tags"])
                elif entity_dict["tags"] is None:
                    entity_dict["tags"] = "[]"
                print(f"Tags field processed: {entity_dict['tags']}")
            
            # 处理其他复杂类型
            for key, value in list(entity_dict.items()):
                if key not in ["properties", "tags"] and isinstance(value, (dict, list)):
                    entity_dict[key] = json.dumps(value)
                elif isinstance(value, UUID):
                    entity_dict[key] = str(value)
                elif key in ["created_at", "updated_at"] and isinstance(value, datetime):
                    entity_dict[key] = value.isoformat()
            
            # 打印即将发送到数据库的entity_dict
            print(f"Entity dict ready for database update: {entity_dict}")
            
            # 更新节点属性
            query = """
            MATCH (e)
            WHERE toString(e.id) = $id
            SET e.name = $name,
                e.type = $type,
                e.description = $description,
                e.properties = $properties,
                e.category = $category,
                e.updated_at = $updated_at
            RETURN e
            """
            # 准备参数
            params = {
                "id": entity_id,
                "name": entity_dict.get("name"),
                "type": entity_dict.get("type"),
                "description": entity_dict.get("description"),
                "properties": entity_dict.get("properties"),
                "category": entity_dict.get("category"),
                "updated_at": datetime.now().isoformat()
            }
            
            # 更新或添加实体类型标签
            type_query = """
            MATCH (e)
            WHERE toString(e.id) = $id
            WITH e, labels(e) as currentLabels
            CALL apoc.create.addLabels(e, [$type])
            YIELD node
            RETURN node
            """
            
            async with self.driver.session(database=self.database) as session:
                # 执行属性更新
                result = await session.run(query,  **params)
                record = await result.single()
                if record:
                    print(f"Successfully updated entity properties")
                else:
                    print(f"Warning: No record returned when updating entity properties")
                
                # 执行类型标签更新
                if "type" in entity_dict and entity_dict["type"]:
                    try:
                        # 首先获取当前节点的所有标签
                        labels_query = """
                        MATCH (e)
                        WHERE toString(e.id) = $id
                        RETURN labels(e) AS labels
                        """
                        
                        labels_result = await session.run(labels_query, id=entity_id)
                        labels_record = await labels_result.single()
                        if labels_record:
                            current_labels = labels_record["labels"]
                            
                            # 移除所有非"Entity"且非新类型的标签
                            for label in current_labels:
                                if label != "Entity" and label != entity_dict["type"]:
                                    remove_query = f"""
                                    MATCH (e)
                                    WHERE toString(e.id) = $id
                                    REMOVE e:{label}
                                    """
                                    await session.run(remove_query, id=entity_id)
                                    print(f"Removed old type label: {label}")
                        
                        # 添加新类型标签
                        add_label_query = f"""
                        MATCH (e)
                        WHERE toString(e.id) = $id
                        SET e:{entity_dict["type"]}
                        RETURN e
                        """
                        
                        await session.run(add_label_query, id=entity_id)
                        print(f"Added new type label: {entity_dict['type']}")
                        
                    except Exception as type_error:
                        print(f"Error updating entity type: {type_error}")
                
                # 直接返回原始对象而不是读取新数据
                # 这避免了验证错误，因为原对象已经是有效的Entity实例
                print(f"Returning original entity object as update result")
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