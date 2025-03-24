# 文件: app/services/knowledge_extractor.py
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
import spacy
from spacy.tokens import Doc, Span
import re

from app.models.entities.entity import Entity
from app.models.relationships.relationship import Relationship
from app.models.documents.source_document import SourceDocument
from app.models.documents.knowledge_trace import KnowledgeTrace
from app.services.interfaces.extractor_interface import ExtractorInterface
from app.db.neo4j_db import Neo4jDatabase


class SpacyNERExtractor(ExtractorInterface):
    """基于spaCy的命名实体识别和关系抽取器"""
    
    def __init__(self, db: Neo4jDatabase, model_name: str = "zh_core_web_trf"):
        self.db = db
        # 加载中文NLP模型
        self.nlp = spacy.load(model_name)
        # 添加自定义组件用于关系提取
        if "relation_extractor" not in self.nlp.pipe_names:
            self.nlp.add_pipe("relation_extractor", last=True)
    
    async def extract_entities(self, document: SourceDocument, text_content: str) -> List[Entity]:
        """从文本中提取实体"""
        # 使用spaCy处理文本
        doc = self.nlp(text_content)
        entities = []
        
        for ent in doc.ents:
            # 将spaCy实体映射到我们的实体模型
            entity_type = self._map_entity_type(ent.label_)
            if not entity_type:
                continue  # 跳过不关心的实体类型
            
            # 创建实体
            entity = Entity(
                type=entity_type,
                name=ent.text,
                description=self._generate_description(ent, doc),
                properties=self._extract_entity_properties(ent),
                source_id=document.id,
                source_type=document.type,
                source_location={
                    "char_offset": ent.start_char,
                    "char_length": len(ent.text),
                    "sentence_id": self._get_sentence_id(doc, ent),
                },
                extraction_method="spacy_ner",
                confidence=ent._.confidence if hasattr(ent._, "confidence") else 0.8,
            )
            
            entities.append(entity)
            
            # 保存到数据库
            await self.db.create(entity)
        
        return entities
    
    async def extract_relationships(self, document: SourceDocument, entities: List[Entity], text_content: str) -> List[Relationship]:
        """从文本中提取实体间的关系"""
        # 使用自定义的关系提取逻辑
        doc = self.nlp(text_content)
        relationships = []
        
        # 简单的规则：如果两个实体在同一个句子中，且中间有特定的模式，则建立关系
        for sent in doc.sents:
            sent_entities = []
            
            # 收集句子中的所有实体
            for entity in entities:
                source_location = entity.source_location
                if source_location is None:
                    continue
                
                start_char = source_location.get("char_offset", 0)
                end_char = start_char + source_location.get("char_length", 0)
                
                # 检查实体是否在当前句子中
                if sent.start_char <= start_char and end_char <= sent.end_char:
                    sent_entities.append(entity)
            
            # 如果句子中至少有两个实体，尝试建立关系
            if len(sent_entities) >= 2:
                for i in range(len(sent_entities) - 1):
                    for j in range(i + 1, len(sent_entities)):
                        source_entity = sent_entities[i]
                        target_entity = sent_entities[j]
                        
                        # 提取两个实体之间的文本
                        source_end = source_entity.source_location["char_offset"] + source_entity.source_location["char_length"]
                        target_start = target_entity.source_location["char_offset"]
                        
                        # 确保正确的顺序
                        if source_end > target_start:
                            source_entity, target_entity = target_entity, source_entity
                            source_end = source_entity.source_location["char_offset"] + source_entity.source_location["char_length"]
                            target_start = target_entity.source_location["char_offset"]
                        
                        between_text = text_content[source_end:target_start]
                        
                        # 尝试识别关系类型
                        relationship_type, confidence = self._identify_relationship(
                            source_entity, target_entity, between_text, sent.text
                        )
                        
                        if relationship_type:
                            relationship = Relationship(
                                type=relationship_type,
                                source_id=source_entity.id,
                                target_id=target_entity.id,
                                properties={
                                    "context": sent.text,
                                    "between_text": between_text,
                                },
                                certainty=confidence,
                                source_id=document.id,
                                source_type=document.type,
                                source_location={
                                    "sentence": sent.text,
                                    "char_offset": sent.start_char,
                                    "char_length": len(sent.text),
                                },
                                extraction_method="rule_based",
                                confidence=confidence,
                            )
                            
                            relationships.append(relationship)
                            
                            # 保存到数据库
                            await self.db.create(relationship)
        
        return relationships
    
    async def create_knowledge_traces(self, document: SourceDocument, entities: List[Entity], relationships: List[Relationship], text_content: str) -> bool:
        """创建知识溯源记录"""
        # 为每个实体和关系创建溯源记录
        for entity in entities:
            if entity.source_location:
                # 计算上下文范围
                char_offset = entity.source_location.get("char_offset", 0)
                char_length = entity.source_location.get("char_length", 0)
                
                # 提取上下文（前后100个字符）
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
                        "content_fingerprint": self._generate_fingerprint(excerpt),
                    },
                )
                
                # 这里应该保存到数据库，但简化起见，我们只返回成功
        
        for relationship in relationships:
            if relationship.source_location:
                # 计算上下文
                char_offset = relationship.source_location.get("char_offset", 0)
                char_length = relationship.source_location.get("char_length", 0)
                
                # 提取上下文
                context_start = max(0, char_offset - 100)
                context_end = min(len(text_content), char_offset + char_length + 100)
                excerpt = text_content[char_offset:char_offset + char_length]
                
                # 创建溯源记录
                trace = KnowledgeTrace(
                    relationship_id=relationship.id,
                    document_id=document.id,
                    location_data=relationship.source_location,
                    context_range={
                        "before_chars": char_offset - context_start,
                        "after_chars": context_end - (char_offset + char_length),
                    },
                    excerpt=excerpt,
                    anchor_type="char_offset",
                    anchor_data={
                        "start_offset": char_offset,
                        "end_offset": char_offset + char_length,
                        "content_fingerprint": self._generate_fingerprint(excerpt),
                    },
                )
                
                # 同样，这里应该保存到数据库
        
        return True
    
    def _map_entity_type(self, spacy_type: str) -> Optional[str]:
        """将spaCy实体类型映射到我们的类型系统"""
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
        return mapping.get(spacy_type)
    
    def _generate_description(self, ent: Span, doc: Doc) -> str:
        """为实体生成简短描述"""
        # 获取实体所在的句子
        sentence = next((sent for sent in doc.sents if ent.start >= sent.start and ent.end <= sent.end), None)
        if sentence:
            return sentence.text
        return ""
    
    def _extract_entity_properties(self, ent: Span) -> Dict[str, Any]:
        """提取实体的额外属性"""
        properties = {}
        
        if ent.label_ == "DATE" or ent.label_ == "TIME":
            # 可以使用如dateparser等库进一步解析日期时间
            properties["date_text"] = ent.text
        
        # 可以根据实体类型添加更多特定属性
        
        return properties
    
    def _get_sentence_id(self, doc: Doc, ent: Span) -> int:
        """获取实体所在的句子ID"""
        for i, sent in enumerate(doc.sents):
            if ent.start >= sent.start and ent.end <= sent.end:
                return i
        return -1
    
    def _identify_relationship(self, source_entity: Entity, target_entity: Entity, between_text: str, sentence: str) -> Tuple[Optional[str], float]:
        """识别两个实体之间的关系类型"""
        # 简单的规则匹配
        # 这里只是示例，实际应用中可能需要更复杂的规则或机器学习方法
        
        # 清理文本
        between_text = between_text.strip().lower()
        
        # 定义一些关系模式
        is_a_patterns = [r"是[一个|种|类型的]*", r"属于", r"归类为"]
        part_of_patterns = [r"包含", r"组成部分", r"包括", r"由.*组成"]
        attribute_of_patterns = [r"的特点", r"的属性", r"的特性"]
        depends_on_patterns = [r"依赖", r"需要", r"基于"]
        
        # 检查模式
        for pattern in is_a_patterns:
            if re.search(pattern, between_text):
                return "is_a", 0.8
        
        for pattern in part_of_patterns:
            if re.search(pattern, between_text):
                return "part_of", 0.7
        
        for pattern in attribute_of_patterns:
            if re.search(pattern, between_text):
                return "attribute_of", 0.7
        
        for pattern in depends_on_patterns:
            if re.search(pattern, between_text):
                return "depends_on", 0.6
        
        # 如果没有匹配到特定模式，根据实体类型进行推测
        if source_entity.type == "person" and target_entity.type == "organization":
            return "works_for", 0.5
        
        if source_entity.type == "concept" and target_entity.type == "concept":
            return "related_to", 0.4
        
        # 如果无法确定关系，返回None
        return None, 0.0
    
    def _generate_fingerprint(self, text: str) -> str:
        """生成文本内容的指纹，用于后续匹配"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
