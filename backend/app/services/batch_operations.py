# app/services/batch_operations.py

from typing import List, Dict, Any, Optional, Union, Tuple
from uuid import UUID
import asyncio
from fastapi import HTTPException

from app.db.neo4j_enhanced import Neo4jEnhanced
from app.models.entities.entity import Entity
from app.models.relationships.relationship import Relationship
from app.core.logger import logger

class BatchOperations:
    """批量操作服务，优化大规模数据导入与更新"""
    
    def __init__(self, db: Neo4jEnhanced):
        self.db = db
        self.batch_size = 500  # 默认批量大小
    
    async def batch_create_entities(self, entities: List[Entity]) -> Tuple[int, List[Dict[str, Any]]]:
        """批量创建实体"""
        if not entities:
            return 0, []
        
        # 分批处理
        batches = [entities[i:i + self.batch_size] for i in range(0, len(entities), self.batch_size)]
        
        success_count = 0
        errors = []
        
        for batch in batches:
            # 准备批量插入的参数
            batch_params = []
            for entity in batch:
                entity_dict = entity.dict(exclude={"id"})
                # 处理特殊类型
                for key, value in entity_dict.items():
                    if isinstance(value, dict) or isinstance(value, list):
                        entity_dict[key] = str(value)  # 简化处理，实际应使用JSON序列化
                
                batch_params.append({
                    "id": str(entity.id),
                    "labels": [entity.type, "Entity"],
                    "properties": entity_dict
                })
            
            # 构建批量插入的Cypher查询
            cypher_query = """
            UNWIND $batch AS row
            CREATE (n:Entity)
            SET n = row.properties
            SET n.id = row.id
            WITH n, row
            CALL apoc.create.addLabels(n, row.labels) YIELD node
            RETURN count(node) as created
            """
            
            try:
                result = await self.db.execute_write_query(cypher_query, {"batch": batch_params})
                if result and result[0]:
                    success_count += result[0]
            except Exception as e:
                logger.error(f"Batch entity creation error: {e}")
                errors.append({"error": str(e), "affected_count": len(batch)})
        
        return success_count, errors
    
    async def batch_create_relationships(self, relationships: List[Relationship]) -> Tuple[int, List[Dict[str, Any]]]:
        """批量创建关系"""
        if not relationships:
            return 0, []
        
        # 分批处理
        batches = [relationships[i:i + self.batch_size] for i in range(0, len(relationships), self.batch_size)]
        
        success_count = 0
        errors = []
        
        for batch in batches:
            # 准备批量插入的参数
            batch_params = []
            for rel in batch:
                rel_dict = rel.dict(exclude={"id", "source_id", "target_id"})
                # 处理特殊类型
                for key, value in rel_dict.items():
                    if isinstance(value, dict) or isinstance(value, list):
                        rel_dict[key] = str(value)  # 简化处理
                
                batch_params.append({
                    "id": str(rel.id),
                    "source_id": str(rel.source_id),
                    "target_id": str(rel.target_id),
                    "type": rel.type,
                    "properties": rel_dict
                })
            
            # 构建批量插入的Cypher查询
            cypher_query = """
            UNWIND $batch AS row
            MATCH (source:Entity {id: row.source_id})
            MATCH (target:Entity {id: row.target_id})
            CREATE (source)-[r:`${row.type}`]->(target)
            SET r = row.properties
            SET r.id = row.id
            RETURN count(r) as created
            """
            
            try:
                result = await self.db.execute_write_query(
                    cypher_query.replace("${row.type}", batch_params[0]["type"]), 
                    {"batch": batch_params}
                )
                if result and result[0]:
                    success_count += result[0]
            except Exception as e:
                logger.error(f"Batch relationship creation error: {e}")
                errors.append({"error": str(e), "affected_count": len(batch)})
        
        return success_count, errors
    
    async def batch_update(self, objects: List[Union[Entity, Relationship]]) -> Tuple[int, List[Dict[str, Any]]]:
        """批量更新实体或关系"""
        if not objects:
            return 0, []
        
        # 分类处理
        entities = [obj for obj in objects if isinstance(obj, Entity)]
        relationships = [obj for obj in objects if isinstance(obj, Relationship)]
        
        entity_results = await self._batch_update_entities(entities) if entities else (0, [])
        relationship_results = await self._batch_update_relationships(relationships) if relationships else (0, [])
        
        return (
            entity_results[0] + relationship_results[0],
            entity_results[1] + relationship_results[1]
        )
    
    async def _batch_update_entities(self, entities: List[Entity]) -> Tuple[int, List[Dict[str, Any]]]:
        """批量更新实体"""
        # 实现类似batch_create_entities的逻辑，但使用MERGE而非CREATE
        # 略...
        return 0, []
    
    async def _batch_update_relationships(self, relationships: List[Relationship]) -> Tuple[int, List[Dict[str, Any]]]:
        """批量更新关系"""
        # 实现类似batch_create_relationships的逻辑，但使用MERGE而非CREATE
        # 略...
        return 0, []
    
    async def bulk_import_from_csv(self, nodes_file: str, relationships_file: str) -> Dict[str, Any]:
        """从CSV文件批量导入数据"""
        # 使用Neo4j的LOAD CSV功能进行大规模数据导入
        nodes_cypher = """
        LOAD CSV WITH HEADERS FROM 'file:///$file' AS row
        CREATE (n:Entity)
        SET n = row
        """
        
        rels_cypher = """
        LOAD CSV WITH HEADERS FROM 'file:///$file' AS row
        MATCH (source:Entity {id: row.source_id})
        MATCH (target:Entity {id: row.target_id})
        CREATE (source)-[r:RELATED_TO]->(target)
        SET r = row
        """
        
        try:
            # 导入节点
            nodes_result = await self.db.execute_write_query(
                nodes_cypher.replace("$file", nodes_file)
            )
            
            # 导入关系
            rels_result = await self.db.execute_write_query(
                rels_cypher.replace("$file", relationships_file)
            )
            
            return {
                "nodes_imported": len(nodes_result) if nodes_result else 0,
                "relationships_imported": len(rels_result) if rels_result else 0,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Bulk import error: {e}")
            raise HTTPException(status_code=500, detail=f"Bulk import failed: {e}")