# app/services/nlp_pipeline.py

import spacy
from spacy.language import Language
from spacy.tokens import Doc, Span
from typing import List, Dict, Any, Optional, Tuple
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

@Language.factory("entity_linker")
class EntityLinkerComponent:
    """实体链接组件，将识别的实体与知识库实体关联"""
    
    def __init__(self, nlp, name):
        self.name = name
        # 加载预训练语言模型用于实体表示
        self.tokenizer = AutoTokenizer.from_pretrained("hfl/chinese-roberta-wwm-ext")
        self.model = AutoModel.from_pretrained("hfl/chinese-roberta-wwm-ext")
        
        # 初始化实体嵌入缓存
        self.entity_embeddings = {}
    
    def __call__(self, doc):
        # 为每个实体计算嵌入并关联到知识库
        for ent in doc.ents:
            # 计算实体文本的嵌入
            embedding = self._get_embedding(ent.text)
            
            # 存储嵌入向量到自定义属性
            ent._.set("embedding", embedding)
            
            # 后续可以实现与知识库实体的关联逻辑
            # 这里简化处理，仅设置一个示例ID
            ent._.set("kb_id", f"entity_{hash(ent.text) % 10000}")
        
        return doc
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """计算文本的语义嵌入"""
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # 使用[CLS]令牌的表示作为整个文本的嵌入
        embedding = outputs.last_hidden_state[:, 0, :].numpy()
        return embedding


class NLPPipeline:
    """NLP处理管道，集成多种语言处理组件"""
    
    def __init__(self, models: Dict[str, str] = None):
        self.models = models or {
            "zh": "zh_core_web_trf",  # 中文Transformer模型
            "en": "en_core_web_trf",   # 英文Transformer模型
        }
        
        # 加载语言模型
        self.nlp_processors = {}
        for lang, model_name in self.models.items():
            try:
                nlp = spacy.load(model_name)
                
                # 注册自定义扩展属性
                if not Doc.has_extension("knowledge_base_id"):
                    Doc.set_extension("knowledge_base_id", default=None)
                
                if not Span.has_extension("embedding"):
                    Span.set_extension("embedding", default=None)
                
                if not Span.has_extension("kb_id"):
                    Span.set_extension("kb_id", default=None)
                
                if not Span.has_extension("confidence"):
                    Span.set_extension("confidence", default=0.0)
                
                # 添加自定义组件
                if "entity_linker" not in nlp.pipe_names:
                    nlp.add_pipe("entity_linker")
                
                self.nlp_processors[lang] = nlp
            except Exception as e:
                print(f"Error loading NLP model {model_name}: {e}")
    
    async def process_text(self, text: str, lang: str = None) -> Doc:
        """处理文本，返回NLP分析结果"""
        # 自动检测语言（简化实现）
        if lang is None:
            # 这里可以实现更复杂的语言检测逻辑
            if any(c for c in text[:100] if '\u4e00' <= c <= '\u9fff'):
                lang = "zh"  # 中文
            else:
                lang = "en"  # 默认英文
        
        # 获取对应的处理器
        nlp = self.nlp_processors.get(lang)
        if not nlp:
            # 回退到英文处理器
            nlp = self.nlp_processors.get("en")
            if not nlp:
                raise ValueError("No available NLP processor")
        
        # 处理文本
        return nlp(text)
    
    async def extract_entities_and_relations(self, text: str, lang: str = None) -> Tuple[List[Dict], List[Dict]]:
        """从文本中提取实体和关系"""
        doc = await self.process_text(text, lang)
        
        # 提取实体
        entities = []
        for ent in doc.ents:
            entity = {
                "text": ent.text,
                "type": ent.label_,
                "start_char": ent.start_char,
                "end_char": ent.end_char,
                "kb_id": ent._.kb_id,
                "confidence": 0.85  # 简化实现，实际系统应计算真实置信度
            }
            entities.append(entity)
        
        # 提取关系（简化实现）
        relations = []
        entity_spans = {(e["start_char"], e["end_char"]): i for i, e in enumerate(entities)}
        
        # 遍历句子查找可能的关系
        for sent in doc.sents:
            sent_entities = []
            
            # 收集句子中的实体
            for key, entity_idx in entity_spans.items():
                start, end = key
                if start >= sent.start_char and end <= sent.end_char:
                    sent_entities.append((entity_idx, start, end))
            
            # 如果句子中有多个实体，尝试识别关系
            if len(sent_entities) >= 2:
                sent_entities.sort(key=lambda x: x[1])  # 按位置排序
                
                for i in range(len(sent_entities) - 1):
                    for j in range(i + 1, len(sent_entities)):
                        idx1, start1, end1 = sent_entities[i]
                        idx2, start2, end2 = sent_entities[j]
                        
                        # 提取两个实体之间的文本
                        between_text = text[end1:start2]
                        
                        # 尝试确定关系类型（简化实现）
                        relation_type, confidence = self._identify_relation(
                            between_text, 
                            entities[idx1]["type"], 
                            entities[idx2]["type"]
                        )
                        
                        if relation_type:
                            relation = {
                                "source": idx1,
                                "target": idx2,
                                "type": relation_type,
                                "text": between_text.strip(),
                                "confidence": confidence
                            }
                            relations.append(relation)
        
        return entities, relations
    
    def _identify_relation(self, text: str, source_type: str, target_type: str) -> Tuple[Optional[str], float]:
        """识别关系类型（简化实现）"""
        # 实际系统应实现更复杂的关系提取逻辑
        text = text.strip().lower()
        
        # 简单规则匹配
        if "是" in text or "属于" in text:
            return "is_a", 0.8
        elif "包含" in text or "组成" in text:
            return "has_part", 0.7
        elif "位于" in text or "在" in text:
            return "located_in", 0.7
        elif "创建" in text or "发明" in text:
            return "created_by", 0.7
        
        # 基于实体类型的推断
        if source_type == "PERSON" and target_type == "ORG":
            return "works_for", 0.5
        elif source_type == "CONCEPT" and target_type == "CONCEPT":
            return "related_to", 0.4
        
        return None, 0.0