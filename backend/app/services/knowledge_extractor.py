# app/services/knowledge_extractor.py

from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4
import asyncio
import spacy
import os

from app.models.entities.entity import Entity
from app.models.relationships.relationship import Relationship
from app.models.documents.source_document import SourceDocument
from app.models.documents.knowledge_trace import KnowledgeTrace
from app.db.neo4j_db import Neo4jDatabase


class SpacyNERExtractor:
    """知识抽取器，负责从文档中提取实体和关系"""
    
    def __init__(self, db: Neo4jDatabase, model_name: str = "zh_core_web_sm"):
        self.db = db
        self.model_name = model_name
        
        # 尝试加载模型，如果失败则使用回退模型
        try:
            self.nlp = spacy.load(model_name)
            print(f"Loaded NLP model: {model_name}")
        except Exception as e:
            print(f"Error loading model {model_name}: {e}")
            try:
                # 尝试加载基础模型
                self.nlp = spacy.load("en_core_web_sm")
                print("Loaded fallback model: en_core_web_sm")
            except:
                # 如果仍然失败，使用空白模型
                print("Using blank model as fallback")
                self.nlp = spacy.blank("en")
    
    async def extract_entities(self, document: SourceDocument, text_content: str) -> List[Entity]:
        """从文本中提取实体
        
        Args:
            document: 源文档
            text_content: 文档文本内容
            
        Returns:
            提取的实体列表
        """
        print(f"Extracting entities from document: {document.title}")
        
        # 限制文本长度以避免处理过大的文档
        max_length = 100000  # 限制为10万个字符
        if len(text_content) > max_length:
            text_content = text_content[:max_length]
            print(f"Text truncated to {max_length} characters")
        
        # 使用spaCy进行实体识别
        doc = self.nlp(text_content)
        entities = []
        
        # 提取实体
        for ent in doc.ents:
            # 映射spaCy实体类型到系统类型
            entity_type = self._map_entity_type(ent.label_)
            
            # 创建实体
            entity = Entity(
                type=entity_type,
                name=ent.text,
                description=self._generate_description(ent, text_content),
                properties={},
                source_id=document.id,
                source_type=document.type,
                source_location={
                    "char_offset": ent.start_char,
                    "char_length": len(ent.text),
                },
                extraction_method="spacy_nlp",
                confidence=0.85,  # 简化，实际应基于置信度计算
            )
            
            # 添加到结果
            entities.append(entity)
            
            # 保存到数据库
            try:
                await self.db.create(entity)
                print(f"Created entity: {entity.name} ({entity.type})")
            except Exception as e:
                print(f"Error saving entity {entity.name}: {e}")
        
        print(f"Extracted {len(entities)} entities")
        return entities
    
    async def extract_relationships(self, document: SourceDocument, entities: List[Entity], text_content: str) -> List[Relationship]:
        """从文本中提取实体间的关系
        
        Args:
            document: 源文档
            entities: 已提取的实体
            text_content: 文档文本内容
            
        Returns:
            提取的关系列表
        """
        print(f"Extracting relationships from document: {document.title}")
        
        # 如果实体少于2个，无法建立关系
        if len(entities) < 2:
            return []
        
        # 使用实体共现方法提取潜在关系
        relationships = []
        
        # 构建句子分割
        doc = self.nlp(text_content)
        sentences = list(doc.sents)
        
        # 基于句子共现建立关系
        for sent in sentences:
            # 在当前句子中找实体
            sent_entities = []
            for entity in entities:
                # 检查实体是否在当前句子范围内
                if entity.source_location:
                    entity_start = entity.source_location.get("char_offset", 0)
                    entity_end = entity_start + entity.source_location.get("char_length", 0)
                    
                    if sent.start_char <= entity_start and entity_end <= sent.end_char:
                        sent_entities.append(entity)
            
            # 如果句子中有多个实体，创建它们之间的关系
            if len(sent_entities) >= 2:
                for i in range(len(sent_entities) - 1):
                    for j in range(i + 1, len(sent_entities)):
                        # 检查是否已存在相同的关系
                        relation_exists = False
                        for rel in relationships:
                            if (rel.source_id == sent_entities[i].id and rel.target_id == sent_entities[j].id) or \
                               (rel.source_id == sent_entities[j].id and rel.target_id == sent_entities[i].id):
                                relation_exists = True
                                break
                        
                        if not relation_exists:
                            # 基于实体类型猜测关系类型
                            relation_type = self._guess_relation_type(
                                sent_entities[i].type, 
                                sent_entities[j].type
                            )
                            
                            # 创建关系
                            relationship = Relationship(
                                type=relation_type,
                                source_id=sent_entities[i].id,
                                target_id=sent_entities[j].id,
                                properties={
                                    "context": sent.text,
                                },
                                bidirectional=False,
                                certainty=0.7,  # 共现关系的确定性较低
                                # 修复：使用文档来源信息
                                source_type=document.type,
                                extraction_method="co_occurrence",
                                confidence=0.7,
                            )
                            
                            # 手动设置source_id属性，避免构造函数中的命名冲突
                            document_id = document.id
                            if isinstance(document_id, UUID):
                                document_id = str(document_id)
                            setattr(relationship, "source_id", document_id)
                            
                            # 添加到结果
                            relationships.append(relationship)
                            
                            # 保存到数据库
                            try:
                                await self.db.create(relationship)
                                print(f"Created relationship: {sent_entities[i].name} --[{relation_type}]--> {sent_entities[j].name}")
                            except Exception as e:
                                print(f"Error saving relationship: {e}")
        
        print(f"Extracted {len(relationships)} relationships")
        return relationships
    
    async def create_knowledge_traces(self, document: SourceDocument, entities: List[Entity], relationships: List[Relationship], text_content: str) -> List[KnowledgeTrace]:
        """创建知识溯源记录
        
        Args:
            document: 源文档
            entities: 提取的实体
            relationships: 提取的关系
            text_content: 文档文本内容
            
        Returns:
            创建的溯源记录列表
        """
        print(f"Creating knowledge traces for document: {document.title}")
        
        traces = []
        
        # 为每个实体创建溯源记录
        for entity in entities:
            if entity.source_location:
                # 计算上下文范围
                char_offset = entity.source_location.get("char_offset", 0)
                char_length = entity.source_location.get("char_length", 0)
                
                # 提取上下文
                context_start = max(0, char_offset - 100)
                context_end = min(len(text_content), char_offset + char_length + 100)
                excerpt = text_content[char_offset:char_offset + char_length]
                
                # 创建溯源记录
                trace = KnowledgeTrace(
                    entity_id=entity.id,
                    document_id=document.id,
                    location_data=entity.source_location,
                    context_range={
                        "before_chars": char_offset - context_start,
                        "after_chars": context_end - (char_offset + char_length),
                    },
                    excerpt=excerpt,
                    anchor_type="char_offset",
                    anchor_data={
                        "start_offset": char_offset,
                        "end_offset": char_offset + char_length,
                        "content_hash": self._generate_fingerprint(excerpt),
                    },
                )
                
                # 添加到结果
                traces.append(trace)
                
                # 这里应该保存到数据库，但目前我们只返回结果
                print(f"Created trace for entity: {entity.name}")
        
        # 为关系创建溯源记录
        # 简化实现，实际系统中可能会更复杂
        
        print(f"Created {len(traces)} knowledge traces")
        return traces
    
    def _map_entity_type(self, spacy_type: str) -> str:
        """将spaCy实体类型映射到系统类型"""
        mapping = {
            "PERSON": "person",
            "ORG": "organization",
            "GPE": "location",
            "LOC": "location",
            "DATE": "time",
            "TIME": "time",
            "MONEY": "concept",
            "PERCENT": "concept",
            "PRODUCT": "concept",
            "EVENT": "event",
            "WORK_OF_ART": "concept",
            "LAW": "concept",
            "LANGUAGE": "concept",
        }
        return mapping.get(spacy_type, "concept")
    
    def _generate_description(self, entity, text_content: str) -> str:
        """生成实体描述"""
        # 简单实现：提取实体所在的句子作为描述
        start = entity.start_char
        
        # 向前寻找句子开始（句号、问号、感叹号之后）
        sentence_start = max(0, start - 200)
        for i in range(start - 1, sentence_start, -1):
            if i < 0:
                break
            if text_content[i] in "。.!?！？":
                sentence_start = i + 1
                break
        
        # 向后寻找句子结束
        sentence_end = min(len(text_content), start + 200)
        for i in range(start, sentence_end):
            if i >= len(text_content):
                break
            if text_content[i] in "。.!?！？":
                sentence_end = i + 1
                break
        
        return text_content[sentence_start:sentence_end].strip()
    
    def _generate_fingerprint(self, text: str) -> str:
        """生成文本指纹，用于内容匹配"""
        import hashlib
        return hashlib.md5(text.encode("utf-8")).hexdigest()
    
    # 文件: backend/app/services/knowledge_extractor.py
    def _guess_relation_type(self, source_type: str, target_type: str) -> str:
        """根据实体类型猜测关系类型"""
        # 扩展关系类型映射
        type_map = {
            # 人物相关
            ("person", "person"): "knows",
            ("person", "organization"): "works_for",
            ("organization", "person"): "employs",
            ("person", "location"): "located_in",
            ("person", "event"): "participated_in",
            ("person", "concept"): "studied",
            ("person", "time"): "lived_during",
            
            # 组织相关
            ("organization", "organization"): "related_to",
            ("organization", "location"): "located_in",
            ("organization", "concept"): "focuses_on",
            ("organization", "time"): "existed_during",
            
            # 概念相关
            ("concept", "concept"): "related_to",
            ("concept", "time"): "developed_in",
            ("concept", "event"): "associated_with",
            
            # 一般关系
            ("event", "time"): "occurred_in",
            ("event", "location"): "occurred_at",
            ("location", "location"): "near",
        }
        
        # 查找匹配的关系类型
        relation_key = (source_type, target_type)
        if relation_key in type_map:
            return type_map[relation_key]
        
        # 基于实体类型的通用规则
        if source_type == target_type:
            return "related_to"
        if source_type == "concept" and target_type != "concept":
            return "describes"
        if target_type == "concept" and source_type != "concept":
            return "described_by"
        
        # 默认关系类型
        return "has_relation"