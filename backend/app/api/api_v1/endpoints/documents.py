# 文件: app/api/api_v1/endpoints/documents.py
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from app.models.documents.source_document import SourceDocument
from app.services.document_processor import DocumentProcessor
from app.db.neo4j_db import Neo4jDatabase
from app.api.deps import get_db
import os
import json

from backend.app.services.knowledge_extractor import SpacyNERExtractor

router = APIRouter()

# Create necessary directories
os.makedirs("./data/documents", exist_ok=True)
os.makedirs("./data/archives", exist_ok=True)

# Initialize mock documents for testing
mock_documents = []

# For development only: Mock implementation of knowledge extractor
class MockKnowledgeExtractor:
    """简化的知识抽取器用于测试"""
    
    def __init__(self, db):
        self.db = db
    
    async def extract_entities(self, document, text_content):
        print(f"Mock extracting entities from document: {document.title}")
        return []
    
    async def extract_relationships(self, document, entities, text_content):
        print(f"Mock extracting relationships from document: {document.title}")
        return []
    
    async def create_knowledge_traces(self, document, entities, relationships, text_content):
        print(f"Mock creating knowledge traces for document: {document.title}")
        return []


# app/api/api_v1/endpoints/documents.py (updated upload method)

@router.post("/upload", response_model=dict)
async def upload_document(
    file: UploadFile = File(...),
    extract_knowledge: bool = Form(False),
    db: Neo4jDatabase = Depends(get_db)
):
    """上传文档并可选地提取知识"""
    # 创建文档处理器
    document_processor = DocumentProcessor()
    
    # 处理文档
    result = await document_processor.process_file(file.file, file.filename)
    
    if result.error:
        raise HTTPException(status_code=400, detail=f"Error processing document: {result.error}")
    
    # 如果需要，提取知识
    entities = []
    relationships = []
    extract_error = None
    
    if extract_knowledge:
        try:
            # 创建知识抽取器
            extractor = SpacyNERExtractor(db)
            
            # 提取实体
            entities = await extractor.extract_entities(result.document, result.text_content)
            
            # 如果至少有两个实体，才提取关系
            if len(entities) >= 2:
                # 提取关系
                relationships = await extractor.extract_relationships(result.document, entities, result.text_content)
                
                # 创建溯源记录
                await extractor.create_knowledge_traces(result.document, entities, relationships, result.text_content)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            extract_error = str(e)
            print(f"Error during knowledge extraction: {e}")
            # 继续处理，即使知识提取失败
    
    # 保存到数据库 - 确保这部分在try块之外，即使知识提取失败也能保存文档
    try:
        # 这里应该实现保存文档到数据库的逻辑
        # 由于我们没有完整的文档保存逻辑，这里仅作为示例
        pass
    except Exception as db_error:
        print(f"Warning: Could not save document to database: {db_error}")
    
    return {
        "document": result.document,
        "extracted_entities": len(entities),
        "extracted_relationships": len(relationships),
        "extraction_error": extract_error,
        "message": "Document processed successfully" + (
            " but knowledge extraction failed: " + extract_error if extract_error else ""
        )
    }


@router.post("/url", response_model=dict)
async def process_url(
    background_tasks: BackgroundTasks,
    url: str = Form(...),
    extract_knowledge: bool = Form(False),
    db: Neo4jDatabase = Depends(get_db)
):
    """处理URL并可选地提取知识"""
    try:
        # 创建文档处理器
        document_processor = DocumentProcessor()
        
        # 处理URL
        result = await document_processor.process_url(url)
        
        if result.error:
            raise HTTPException(status_code=400, detail=f"Error processing URL: {result.error}")
        
        # Add to mock documents for testing
        mock_documents.append(result.document)
        
        # Background knowledge extraction similar to document upload
        if extract_knowledge:
            # Implementation similar to upload_document
            pass
        
        return {
            "document": result.document,
            "extracted_entities": 0,
            "extracted_relationships": 0,
            "message": "URL processed successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing URL: {str(e)}")


@router.get("/", response_model=List[dict])
async def read_documents(
    skip: int = 0,
    limit: int = 100,
    document_type: Optional[str] = None,
    title: Optional[str] = Query(None, description="文档标题（支持模糊匹配）"),
    db: Neo4jDatabase = Depends(get_db)
):
    """获取文档列表，支持分页和过滤"""
    # Return mock documents for testing
    filtered_docs = mock_documents
    
    # Apply filters
    if document_type:
        filtered_docs = [doc for doc in filtered_docs if doc.type == document_type]
    
    if title:
        filtered_docs = [doc for doc in filtered_docs if title.lower() in doc.title.lower()]
    
    # Apply pagination
    paginated_docs = filtered_docs[skip:skip+limit]
    
    # Convert to dict for serialization
    result = []
    for doc in paginated_docs:
        doc_dict = doc.dict()
        # Convert UUID to string for JSON serialization
        doc_dict["id"] = str(doc_dict["id"])
        if "source_id" in doc_dict and doc_dict["source_id"]:
            doc_dict["source_id"] = str(doc_dict["source_id"])
        result.append(doc_dict)
    
    return result


@router.get("/{document_id}", response_model=dict)
async def read_document(
    document_id: UUID,
    db: Neo4jDatabase = Depends(get_db)
):
    """获取指定ID的文档"""
    # Search in mock documents
    for doc in mock_documents:
        if doc.id == document_id:
            doc_dict = doc.dict()
            doc_dict["id"] = str(doc_dict["id"])
            if "source_id" in doc_dict and doc_dict["source_id"]:
                doc_dict["source_id"] = str(doc_dict["source_id"])
            return doc_dict
    
    raise HTTPException(status_code=404, detail="Document not found")


@router.delete("/{document_id}", response_model=bool)
async def delete_document(
    document_id: UUID,
    db: Neo4jDatabase = Depends(get_db)
):
    """删除文档"""
    global mock_documents
    # Find and remove from mock documents
    for i, doc in enumerate(mock_documents):
        if doc.id == document_id:
            mock_documents.pop(i)
            return True
    
    raise HTTPException(status_code=404, detail="Document not found")


@router.get("/{document_id}/preview")
async def preview_document(
    document_id: UUID,
    db: Neo4jDatabase = Depends(get_db)
):
    """预览文档内容"""
    # Find in mock documents
    for doc in mock_documents:
        if doc.id == document_id:
            # In a real implementation, we would load content from file_path
            return {"content": f"Preview content for document: {doc.title}"}
    
    raise HTTPException(status_code=404, detail="Document not found")


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    db: Neo4jDatabase = Depends(get_db)
):
    """下载文档"""
    # Find in mock documents
    for doc in mock_documents:
        if doc.id == document_id:
            # In a real implementation, we would return a FileResponse
            raise HTTPException(status_code=501, detail="Download functionality not implemented yet")
    
    raise HTTPException(status_code=404, detail="Document not found")


@router.post("/{document_id}/extract", response_model=dict)
async def extract_knowledge(
    document_id: UUID,
    db: Neo4jDatabase = Depends(get_db)
):
    """从文档提取知识"""
    # Find in mock documents
    for doc in mock_documents:
        if doc.id == document_id:
            return {
                "document_id": str(document_id),
                "extracted_entities": 0,
                "extracted_relationships": 0,
                "message": "Knowledge extraction would be performed here"
            }
    
    raise HTTPException(status_code=404, detail="Document not found")


@router.get("/{document_id}/export")
async def export_document(
    document_id: UUID,
    db: Neo4jDatabase = Depends(get_db)
):
    """导出文档及其关联知识"""
    # Find in mock documents
    for doc in mock_documents:
        if doc.id == document_id:
            return {
                "document_id": str(document_id),
                "metadata": doc.metadata,
                "knowledge": {
                    "entities": [],
                    "relationships": []
                }
            }
    
    raise HTTPException(status_code=404, detail="Document not found")