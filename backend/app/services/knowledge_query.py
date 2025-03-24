# 文件: app/services/knowledge_query.py
from typing import Dict, Any, List, Optional, Union
from uuid import UUID

from app.models.entities.entity import Entity
from app.models.relationships.relationship import Relationship
from app.models.documents.source_document import SourceDocument
from app.models.documents.knowledge_trace import KnowledgeTrace
from app.services.interfaces.query_interface import QueryInterface
from app.db.neo4j_db import Neo4jDatabase


class KnowledgeQueryService(QueryInterface):
    """知识查询服务，实现知识图谱的查询和溯源功能"""
    
    def __init__(self, db: Neo4jDatabase):
        self.db = db
    
    async def find_entities(self, query: Dict[str, Any]) -> List[Entity]:
        """根据条件查找实体"""
        # 构建Cypher查询
        conditions = []
        params = {}
        
        for key, value in query.items():
            if key == "type":
                conditions.append(f"e:`{value}`")
            elif key == "name":
                conditions.append("e.name CONTAINS $name")
                params["name"] = value
            elif key == "property":
                # 支持属性查询，格式: property.key=value
                prop_key, prop_value = value.split('=')
                conditions.append(f"e.properties @> '{{\\"{prop_key}\\":\\"{prop_value}\\"}}'")
            elif key == "tag":
                conditions.append("$tag IN e.tags")
                params["tag"] = value
        
        cypher_query = "MATCH (e:Entity)"
        if conditions:
            cypher_query += " WHERE " + " AND ".join(conditions)
        cypher_query += " RETURN e LIMIT 100"
        
        # 执行查询
        results = []
        async with self.db.driver.session(database=self.db.database) as session:
            result = await session.run(cypher_query, **params)
            async for record in result:
                node = record["e"]
                # 将Neo4j节点转换为Entity对象
                entity = self._node_to_entity(node)
                results.append(entity)
        
        return results
    
    async def find_relationships(self, query: Dict[str, Any]) -> List[Relationship]:
        """根据条件查找关系"""
        # 构建Cypher查询
        conditions = []
        params = {}
        
        if "source_id" in query:
            conditions.append("startNode(r).id = $source_id")
            params["source_id"] = str(query["source_id"])
        
        if "target_id" in query:
            conditions.append("endNode(r).id = $target_id")
            params["target_id"] = str(query["target_id"])
        
        if "type" in query:
            conditions.append(f"type(r) = '{query['type']}'")
        
        cypher_query = "MATCH ()-[r]->()"
        if conditions:
            cypher_query += " WHERE " + " AND ".join(conditions)
        cypher_query += " RETURN r, startNode(r) as source, endNode(r) as target LIMIT 100"
        
        # 执行查询
        results = []
        async with self.db.driver.session(database=self.db.database) as session:
            result = await session.run(cypher_query, **params)
            async for record in result:
                rel = record["r"]
                source = record["source"]
                target = record["target"]
                # 将Neo4j关系转换为Relationship对象
                relationship = self._rel_to_relationship(rel, source, target)
                results.append(relationship)
        
        return results
    
    async def get_entity_context(self, entity_id: UUID) -> List[Dict[str, Any]]:
        """获取实体的上下文信息：相关实体和关系"""
        # 构建Cypher查询，获取与实体直接相关的其他实体和关系
        cypher_query = """
        MATCH (e:Entity {id: $entity_id})-[r]-(related)
        RETURN e, r, related
        LIMIT 100
        """
        
        context = []
        async with self.db.driver.session(database=self.db.database) as session:
            result = await session.run(cypher_query, entity_id=str(entity_id))
            async for record in result:
                rel = record["r"]
                related = record["related"]
                
                # 将相关实体和关系添加到上下文
                context.append({
                    "relationship": self._rel_to_relationship(rel, None, None),
                    "related_entity": self._node_to_entity(related)
                })
        
        return context
    
    async def trace_knowledge(self, entity_id: Optional[UUID] = None, relationship_id: Optional[UUID] = None) -> List[KnowledgeTrace]:
        """追溯知识来源，获取知识溯源记录"""
        # 根据实体ID或关系ID查询溯源记录
        if entity_id:
            # 查询与实体关联的溯源记录
            # 这里假设有一个存储溯源记录的数据库表或集合
            traces = [
                # 示例溯源记录
                KnowledgeTrace(
                    id=UUID("a1b2c3d4-e5f6-4a5b-9c3d-2e1f0a9b8c7d"),
                    entity_id=entity_id,
                    document_id=UUID("e37f0136-7dc8-4dc9-92d7-b40b98e1a63d"),
                    location_data={
                        "page": 5,
                        "paragraph": 2,
                        "char_offset": 120,
                        "char_length": 45
                    },
                    context_range={
                        "before_chars": 100,
                        "after_chars": 100
                    },
                    excerpt="知识图谱是一种表示知识的图结构，由节点和边组成，节点表示实体，边表示实体间的关系。",
                    anchor_type="char_offset",
                    anchor_data={
                        "start_offset": 120,
                        "end_offset": 165,
                        "content_fingerprint": "哈希值用于确认内容匹配"
                    }
                )
            ]
            return traces
        
        elif relationship_id:
            # 查询与关系关联的溯源记录
            traces = [
                # 示例溯源记录
                KnowledgeTrace(
                    id=UUID("b2c3d4e5-f6a7-5b6c-8d9e-3f1g0a2b3c4d"),
                    relationship_id=relationship_id,
                    document_id=UUID("e37f0136-7dc8-4dc9-92d7-b40b98e1a63d"),
                    location_data={
                        "page": 7,
                        "paragraph": 3,
                        "char_offset": 210,
                        "char_length": 30
                    },
                    context_range={
                        "before_chars": 100,
                        "after_chars": 100
                    },
                    excerpt="知识图谱是知识表示和知识库的一种形式。",
                    anchor_type="char_offset",
                    anchor_data={
                        "start_offset": 210,
                        "end_offset": 240,
                        "content_fingerprint": "哈希值用于确认内容匹配"
                    }
                )
            ]
            return traces
        
        # 如果都没有提供，返回空列表
        return []
    
    async def query_by_natural_language(self, query: str) -> Dict[str, Any]:
        """自然语言查询知识图谱"""
        # 这是一个复杂功能的简化实现
        # 实际实现可能需要NLP技术将自然语言转换为图查询
        
        # 简单的关键词提取
        keywords = query.lower().split()
        
        # 根据关键词查找相关实体
        entities = []
        for keyword in keywords:
            if len(keyword) > 2:  # 忽略太短的关键词
                found_entities = await self.find_entities({"name": keyword})
                entities.extend(found_entities)
        
        # 如果找到实体，获取相关关系
        relationships = []
        for entity in entities:
            context = await self.get_entity_context(entity.id)
            for item in context:
                relationships.append(item["relationship"])
        
        return {
            "query": query,
            "entities": entities,
            "relationships": relationships,
            "interpretation": f"查询 '{query}' 被解释为查找包含关键词的实体及其关系。"
        }
    
    def _node_to_entity(self, node) -> Entity:
        """将Neo4j节点转换为Entity对象"""
        # 提取属性
        props = dict(node)
        
        # 处理特殊类型
        for key, value in props.items():
            if isinstance(value, str) and (key == "properties" or key == "source_location"):
                try:
                    import json
                    props[key] = json.loads(value)
                except:
                    pass
        
        # 创建Entity对象
        return Entity(**props)
    
    def _rel_to_relationship(self, rel, source_node=None, target_node=None) -> Relationship:
        """将Neo4j关系转换为Relationship对象"""
        # 提取属性
        props = dict(rel)
        
        # 添加关系类型
        props["type"] = rel.type
        
        # 添加源和目标实体ID
        if source_node:
            props["source_id"] = source_node.get("id", "")
        
        if target_node:
            props["target_id"] = target_node.get("id", "")
        
        # 处理特殊类型
        for key, value in props.items():
            if isinstance(value, str) and (key == "properties" or key == "source_location"):
                try:
                    import json
                    props[key] = json.loads(value)
                except:
                    pass
        
        # 创建Relationship对象
        return Relationship(**props)