# app/services/knowledge_extractor.py

from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4
import asyncio

from app.models.entities.entity import Entity
from app.models.relationships.relationship import Relationship
from app.models.documents.source_document import SourceDocument
from app.models.documents.knowledge_trace import KnowledgeTrace
from app.services.nlp_pipeline import NLPPipeline
from app.db.neo4j_db import Neo4jDatabase


class KnowledgeExtractor:
    """知识抽取器，负责从文档中提取实体和关系"""
    
    def __init__(self, db: Neo4jDatabase, nlp_pipeline: NLPPipeline = None):
        self.db = db
        self.nlp_pipeline = nlp_pipeline or NLPPipeline()
    
    async def extract_from_document(self, document: SourceDocument, text_content: str) -> Dict[str, Any]:
        """从文档中提取完整知识"""
        # 步骤1：提取实体和关系
        entities, relations = await self.nlp_pipeline.extract_entities_and_relations(text_content)
        
        # 步骤2：创建实体模型
        entity_models = []
        entity_id_map = {}  # 用于映射提取的实体索引到UUID
        
        for entity_data in entities:
            entity = Entity(
                type=self._map_entity_type(entity_data["type"]),
                name=entity_data["text"],
                description=self._generate_description(entity_data, text_content),
                properties={},
                source_id=document.id,
                source_type=document.type,
                source_location={
                    "char_offset": entity_data["start_char"],
                    "char_length": len(entity_data["text"]),
                },
                extraction_method="spacy_nlp",
                confidence=entity_data["confidence"],
            )
            
            # 保存到数据库
            try:
                saved_entity = await self.db.create(entity)
                entity_models.append(saved_entity)
                entity_id_map[entities.index(entity_data)] = saved_entity.id
            except Exception as e:
                print(f"Error saving entity: {e}")
        
        # 步骤3：创建关系模型
        relationship_models = []
        
        for relation_data in relations:
            # 获取源实体和目标实体ID
            source_idx = relation_data["source"]
            target_idx = relation_data["target"]
            
            if source_idx in entity_id_map and target_idx in entity_id_map:
                relationship = Relationship(
                    type=relation_data["type"],
                    source_id=entity_id_map[source_idx],
                    target_id=entity_id_map[target_idx],
                    properties={
                        "text": relation_data["text"],
                    },
                    bidirectional=False,  # 默认为单向关系
                    certainty=relation_data["confidence"],
                    source_id=document.id,
                    source_type=document.type,
                    extraction_method="rule_based",
                    confidence=relation_data["confidence"],
                )
                
                # 保存到数据库
                try:
                    saved_relationship = await self.db.create(relationship)
                    relationship_models.append(saved_relationship)
                except Exception as e:
                    print(f"Error saving relationship: {e}")
        
        # 步骤4：创建知识溯源记录
        await self.create_knowledge_traces(document, entity_models, relationship_models, text_content)
        
        return {
            "document_id": document.id,
            "entities": entity_models,
            "relationships": relationship_models,
            "entities_count": len(entity_models),
            "relationships_count": len(relationship_models),
        }
    
    async def create_knowledge_traces(self, document: SourceDocument, 
                                     entities: List[Entity], 
                                     relationships: List[Relationship], 
                                     text_content: str) -> List[KnowledgeTrace]:
        """创建知识溯源记录"""
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
                
                # 保存到数据库（实际实现中）
                traces.append(trace)
        
        # 类似地，为关系创建溯源记录
        # 省略类似实现...
        
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
    
    def _generate_description(self, entity_data: Dict[str, Any], text_content: str) -> str:
        """生成实体描述"""
        # 简单实现：提取实体所在的句子作为描述
        start = entity_data["start_char"]
        
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