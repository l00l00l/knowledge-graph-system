# app/services/nlp_query_processor.py

from typing import Dict, Any, List, Optional, Tuple
import re
import spacy
from fastapi import HTTPException
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

from app.core.logger import logger

class NLPQueryProcessor:
    """自然语言查询处理器，将自然语言转换为结构化查询"""
    
    def __init__(self, model_path: str = "t5-base"):
        """初始化NLP查询处理器
        
        Args:
            model_path: 预训练模型路径
        """
        # 加载spaCy模型用于基础NLP任务
        try:
            self.nlp = spacy.load("zh_core_web_trf")
        except:
            # 回退到较小的模型
            self.nlp = spacy.load("zh_core_web_sm")
        
        # 加载Transformer模型用于复杂查询转换
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
        except Exception as e:
            logger.warning(f"Failed to load transformer model: {e}. Using rule-based fallback.")
            self.tokenizer = None
            self.model = None
    
    async def process_query(self, query_text: str) -> Dict[str, Any]:
        """处理自然语言查询，返回结构化表示"""
        # 基础NLP处理
        doc = self.nlp(query_text)
        
        # 尝试识别查询意图
        intent = self._identify_intent(doc)
        
        # 提取查询参数
        parameters = self._extract_parameters(doc, intent)
        
        # 如果有高级模型，尝试使用模型进行更精确的理解
        if self.model and self.tokenizer and intent["type"] in ["complex_relation", "multi_hop"]:
            enhanced_parameters = await self._enhance_with_transformer(query_text, intent)
            if enhanced_parameters:
                parameters.update(enhanced_parameters)
        
        return {
            "original_query": query_text,
            "intent": intent["type"],
            "confidence": intent["confidence"],
            "parameters": parameters,
            "entities": [
                {"text": ent.text, "type": ent.label_, "start": ent.start_char, "end": ent.end_char}
                for ent in doc.ents
            ]
        }
    
    def _identify_intent(self, doc) -> Dict[str, Any]:
        """识别查询意图"""
        query_text = doc.text.lower()
        
        # 简单规则匹配
        if any(word in query_text for word in ["是什么", "定义", "概念", "介绍"]):
            return {"type": "entity_definition", "confidence": 0.8}
        elif any(word in query_text for word in ["关系", "联系", "连接"]):
            return {"type": "relationship_query", "confidence": 0.8}
        elif any(word in query_text for word in ["列出", "所有", "找到"]):
            return {"type": "entity_listing", "confidence": 0.7}
        elif any(phrase in query_text for phrase in ["通过", "经过", "之间的路径"]):
            return {"type": "path_finding", "confidence": 0.9}
        elif len(re.findall(r"和|与|以及", query_text)) >= 2:
            return {"type": "multi_hop", "confidence": 0.6}
        elif any(word in query_text for word in ["为什么", "原因", "如何"]):
            return {"type": "complex_relation", "confidence": 0.6}
        else:
            return {"type": "general_query", "confidence": 0.5}
    
    def _extract_parameters(self, doc, intent: Dict[str, Any]) -> Dict[str, Any]:
        """提取查询参数"""
        parameters = {}
        
        # 根据意图类型提取不同参数
        if intent["type"] == "entity_definition":
            # 查找主实体
            for ent in doc.ents:
                if ent.label_ in ["PERSON", "ORG", "GPE", "PRODUCT", "EVENT", "WORK_OF_ART"]:
                    parameters["target_entity"] = ent.text
                    break
            
            if "target_entity" not in parameters:
                # 尝试使用依存句法提取焦点名词
                for token in doc:
                    if token.dep_ in ["nsubj", "dobj"] and token.pos_ == "NOUN":
                        parameters["target_entity"] = token.text
                        break
        
        elif intent["type"] == "relationship_query":
            # 提取关系的两个实体
            entities = []
            for ent in doc.ents:
                entities.append({"text": ent.text, "type": ent.label_})
            
            if len(entities) >= 2:
                parameters["source_entity"] = entities[0]["text"]
                parameters["target_entity"] = entities[1]["text"]
            elif len(entities) == 1:
                parameters["source_entity"] = entities[0]["text"]
        
        # 其他意图类型的参数提取...
        
        return parameters
    
    async def _enhance_with_transformer(self, query_text: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """使用Transformer模型增强查询理解"""
        try:
            # 准备输入
            input_text = f"Convert to query: {query_text}"
            input_ids = self.tokenizer.encode(input_text, return_tensors="pt")
            
            # 生成输出
            with torch.no_grad():
                output_ids = self.model.generate(
                    input_ids,
                    max_length=100,
                    num_beams=5,
                    early_stopping=True
                )
            
            # 解码输出
            output_text = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
            
            # 解析输出为结构化参数
            # 这里需要根据输出格式做具体解析
            # 简化实现：
            if "entity:" in output_text:
                entity_match = re.search(r"entity:\s*(.+?)(?:\s|$)", output_text)
                if entity_match:
                    return {"enhanced_entity": entity_match.group(1)}
            
            return {}
        except Exception as e:
            logger.error(f"Transformer enhancement failed: {e}")
            return {}