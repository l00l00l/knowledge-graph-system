# app/services/nlp_service.py

from typing import Dict, Any, List
import spacy


class NLPService:
    """自然语言处理服务，负责文本分析、意图识别等"""
    
    def __init__(self, model_name: str = "zh_core_web_sm"):
        """初始化NLP服务
        
        Args:
            model_name: spaCy模型名称
        """
        self.nlp = spacy.load(model_name)
    
    async def analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """分析查询意图
        
        Args:
            query: 用户查询文本
            
        Returns:
            包含意图类型和参数的字典
        """
        # 简单的规则匹配实现，实际可以使用更复杂的意图识别模型
        query_lower = query.lower()
        
        # 检测实体搜索意图
        if any(word in query_lower for word in ["查找", "搜索", "寻找"]):
            return {
                "type": "entity_search",
                "parameters": self._extract_entity_search_params(query)
            }
        
        # 检测关系查询意图
        elif any(word in query_lower for word in ["关系", "联系", "连接"]):
            return {
                "type": "relationship_query",
                "parameters": self._extract_relationship_query_params(query)
            }
        
        # 检测上下文探索意图
        elif any(word in query_lower for word in ["上下文", "相关", "周围"]):
            return {
                "type": "context_explore",
                "parameters": self._extract_context_explore_params(query)
            }
        
        # 检测溯源查询意图
        elif any(word in query_lower for word in ["来源", "出处", "溯源"]):
            return {
                "type": "provenance_trace",
                "parameters": self._extract_provenance_trace_params(query)
            }
        
        # 默认为通用查询
        else:
            return {
                "type": "general_query",
                "parameters": {"query_text": query}
            }
    
    def _extract_entity_search_params(self, query: str) -> Dict[str, Any]:
        """提取实体搜索参数"""
        # 使用NLP进行参数提取，这里为简化实现
        doc = self.nlp(query)
        
        params = {"query_text": query}
        
        # 尝试提取实体类型
        for token in doc:
            if token.text in ["概念", "人物", "组织", "地点", "时间", "事件"]:
                params["type"] = token.text
        
        # 尝试提取实体名称
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE", "DATE", "EVENT"]:
                params["name"] = ent.text
        
        return params
    
    def _extract_relationship_query_params(self, query: str) -> Dict[str, Any]:
        """提取关系查询参数"""
        # 使用NLP提取关系参数，简化实现
        doc = self.nlp(query)
        
        params = {"query_text": query}
        entities = []
        
        # 提取查询中的实体作为关系的端点
        for ent in doc.ents:
            entities.append(ent.text)
        
        if len(entities) >= 2:
            params["source_name"] = entities[0]
            params["target_name"] = entities[1]
        
        return params
    
    def _extract_context_explore_params(self, query: str) -> Dict[str, Any]:
        """提取上下文探索参数"""
        doc = self.nlp(query)
        
        params = {"query_text": query}
        
        # 提取查询中的第一个实体作为上下文中心
        for ent in doc.ents:
            params["entity_name"] = ent.text
            break
        
        return params
    
    def _extract_provenance_trace_params(self, query: str) -> Dict[str, Any]:
        """提取溯源查询参数"""
        doc = self.nlp(query)
        
        params = {"query_text": query}
        
        # 提取查询中的第一个实体作为溯源目标
        for ent in doc.ents:
            params["entity_name"] = ent.text
            break
        
        return params