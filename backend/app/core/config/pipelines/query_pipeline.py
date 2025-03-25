# app/core/pipelines/query_pipeline.py

from typing import Dict, Any, List, Optional
from uuid import UUID

from app.services.query_service import QueryService
from app.services.nlp_service import NLPService
from app.services.provenance_service import ProvenanceService


class QueryPipeline:
    """查询处理流水线，协调自然语言处理和知识图谱查询"""
    
    def __init__(self, query_service: QueryService, 
                nlp_service: NLPService,
                provenance_service: ProvenanceService):
        self.query_service = query_service
        self.nlp_service = nlp_service
        self.provenance_service = provenance_service
    
    async def process_query(self, query_text: str) -> Dict[str, Any]:
        """处理自然语言查询"""
        # 分析查询意图
        query_intent = await self.nlp_service.analyze_query_intent(query_text)
        
        # 根据意图类型执行不同查询策略
        if query_intent["type"] == "entity_search":
            # 实体搜索
            result = await self.query_service.find_entities(query_intent["parameters"])
            
        elif query_intent["type"] == "relationship_query":
            # 关系查询
            result = await self.query_service.find_relationships(query_intent["parameters"])
            
        elif query_intent["type"] == "context_explore":
            # 上下文探索
            entity_id = query_intent["parameters"].get("entity_id")
            if entity_id:
                result = await self.query_service.get_entity_context(UUID(entity_id))
            else:
                result = {"error": "Missing entity_id for context exploration"}
                
        elif query_intent["type"] == "provenance_trace":
            # 溯源查询
            entity_id = query_intent["parameters"].get("entity_id")
            relationship_id = query_intent["parameters"].get("relationship_id")
            
            if entity_id:
                traces = await self.provenance_service.find_traces(entity_id=UUID(entity_id))
            elif relationship_id:
                traces = await self.provenance_service.find_traces(relationship_id=UUID(relationship_id))
            else:
                traces = []
                
            result = {
                "query": query_text,
                "traces": traces
            }
        
        else:
            # 默认查询
            result = await self.query_service.query_by_natural_language(query_text)
        
        return {
            "query": query_text,
            "intent": query_intent,
            "result": result
        }