# app/services/query_converter.py

from typing import Dict, Any, List, Optional, Tuple
import re
from fastapi import HTTPException

from app.services.nlp_query_processor import NLPQueryProcessor
from app.core.logger import logger

class QueryConverter:
    """查询转换器，将自然语言查询转换为优化的Cypher查询"""
    
    def __init__(self, nlp_processor: NLPQueryProcessor):
        self.nlp_processor = nlp_processor
        # 查询模板库
        self.query_templates = {
            "entity_definition": """
            MATCH (e:{entity_type} {{name: $entity_name}})
            OPTIONAL MATCH (e)-[r]-(related)
            RETURN e as entity, collect(distinct r) as relationships, collect(distinct related) as related_entities
            """,
            
            "relationship_query": """
            MATCH path = (source)-[r*1..{depth}]-(target)
            WHERE source.name = $source_name AND target.name = $target_name
            RETURN path, relationships(path) as rels
            """,
            
            "entity_listing": """
            MATCH (e:{entity_type})
            WHERE {conditions}
            RETURN e
            LIMIT {limit}
            """,
            
            "path_finding": """
            MATCH path = shortestPath((source)-[*1..{max_depth}]-(target))
            WHERE source.name = $source_name AND target.name = $target_name
            RETURN path
            """,
            
            "multi_hop": """
            MATCH (start:{start_type} {{name: $start_name}})
            MATCH (inter:{inter_type} {{name: $inter_name}})
            MATCH (end:{end_type} {{name: $end_name}})
            MATCH path1 = (start)-[r1*1..{depth}]-(inter)
            MATCH path2 = (inter)-[r2*1..{depth}]-(end)
            RETURN path1, path2
            """,
            
            "general_query": """
            MATCH (e)
            WHERE e.name CONTAINS $query_text OR e.description CONTAINS $query_text
            RETURN e
            LIMIT 10
            """
        }
    
    async def convert_to_cypher(self, query_text: str) -> Dict[str, Any]:
        """将自然语言查询转换为Cypher查询和参数"""
        # 处理自然语言查询
        parsed_query = await self.nlp_processor.process_query(query_text)
        
        # 根据意图和参数生成Cypher查询
        intent_type = parsed_query["intent"]
        parameters = parsed_query["parameters"]
        
        if intent_type in self.query_templates:
            template = self.query_templates[intent_type]
            cypher_query, query_params = self._fill_template(template, intent_type, parameters)
        else:
            # 回退到通用查询
            template = self.query_templates["general_query"]
            cypher_query, query_params = self._fill_template(template, "general_query", 
                                                           {"query_text": query_text})
        
        # 查询优化
        optimized_query = self._optimize_query(cypher_query)
        
        return {
            "original_query": query_text,
            "parsed_query": parsed_query,
            "cypher_query": optimized_query,
            "query_params": query_params
        }
    
    def _fill_template(self, template: str, intent_type: str, parameters: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """填充查询模板"""
        query_params = {}
        
        # 根据意图类型填充不同模板
        if intent_type == "entity_definition":
            entity_name = parameters.get("target_entity", "")
            entity_type = "Entity"  # 默认类型，实际应根据实体名推断
            
            filled_template = template.replace("{entity_type}", entity_type)
            query_params["entity_name"] = entity_name
        
        elif intent_type == "relationship_query":
            source_name = parameters.get("source_entity", "")
            target_name = parameters.get("target_entity", "")
            depth = parameters.get("depth", 2)
            
            filled_template = template.replace("{depth}", str(depth))
            query_params["source_name"] = source_name
            query_params["target_name"] = target_name
        
        # 其他意图类型的模板填充...
        else:
            # 通用查询
            filled_template = template
            query_params["query_text"] = parameters.get("query_text", "")
        
        return filled_template, query_params
    
    def _optimize_query(self, cypher_query: str) -> str:
        """优化Cypher查询"""
        # 简单优化：添加索引提示
        optimized = cypher_query
        
        # 添加USING INDEX提示
        if "WHERE" in optimized and "name" in optimized:
            # 检查是否有适合使用索引的模式
            if re.search(r"WHERE\s+\w+\.name\s*=", optimized):
                # 这是一个可能使用索引的场景
                optimized = optimized.replace(
                    "WHERE", 
                    "USING INDEX e:Entity(name) WHERE"
                )
        
        # 限制结果数量以提高性能
        if "LIMIT" not in optimized:
            optimized += "\nLIMIT 100"
        
        return optimized