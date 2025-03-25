# app/core/pipelines/knowledge_extraction_pipeline.py

from typing import Dict, Any, List, Optional
from uuid import UUID

from app.models.documents.source_document import SourceDocument
from app.services.document_processor import DocumentProcessor
from app.services.knowledge_extractor import KnowledgeExtractor
from app.services.provenance_service import ProvenanceService
from app.db.neo4j_db import Neo4jDatabase


class KnowledgeExtractionPipeline:
    """知识抽取处理流水线，协调文档处理和知识抽取过程"""
    
    def __init__(self, document_processor: DocumentProcessor, 
                knowledge_extractor: KnowledgeExtractor,
                provenance_service: ProvenanceService,
                db: Neo4jDatabase):
        self.document_processor = document_processor
        self.knowledge_extractor = knowledge_extractor
        self.provenance_service = provenance_service
        self.db = db
    
    async def process_document(self, document_id: UUID) -> Dict[str, Any]:
        """处理文档并抽取知识"""
        # 获取文档
        document = await self.db.get_document(document_id)
        if not document:
            raise ValueError(f"Document not found: {document_id}")
        
        # 提取文本内容
        text_content = await self.document_processor.extract_content(document_id)
        
        # 抽取实体
        entities = await self.knowledge_extractor.extract_entities(document, text_content)
        
        # 抽取关系
        relationships = await self.knowledge_extractor.extract_relationships(document, entities, text_content)
        
        # 创建溯源记录
        await self.knowledge_extractor.create_knowledge_traces(document, entities, relationships, text_content)
        
        return {
            "document_id": document_id,
            "entities_count": len(entities),
            "relationships_count": len(relationships),
            "entities": entities,
            "relationships": relationships
        }
    
    async def process_batch(self, document_ids: List[UUID]) -> List[Dict[str, Any]]:
        """批处理多个文档"""
        results = []
        for doc_id in document_ids:
            try:
                result = await self.process_document(doc_id)
                results.append(result)
            except Exception as e:
                results.append({
                    "document_id": doc_id,
                    "error": str(e)
                })
        return results