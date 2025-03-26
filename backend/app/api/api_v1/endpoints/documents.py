# 文件: app/api/api_v1/endpoints/documents.py
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from app.models.documents.source_document import SourceDocument
from app.services.document_processor import DocumentProcessor
from app.services.knowledge_extractor import SpacyNERExtractor
from app.db.neo4j_db import Neo4jDatabase
from app.api.deps import get_db

router = APIRouter()


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
    if extract_knowledge:
        try:
            # 创建知识抽取器
            extractor = SpacyNERExtractor(db)
            
            # 提取实体
            entities = await extractor.extract_entities(result.document, result.text_content)
            
            # 提取关系
            relationships = await extractor.extract_relationships(result.document, entities, result.text_content)
            
            # 创建溯源记录
            await extractor.create_knowledge_traces(result.document, entities, relationships, result.text_content)
        except Exception as e:
            print(f"Error during knowledge extraction: {e}")
            # 继续处理，即使知识提取失败
    
    return {
        "document": result.document,
        "extracted_entities": len(entities),
        "extracted_relationships": len(relationships),
        "message": "Document processed successfully"
    }


@router.post("/url", response_model=dict)
async def process_url(
    url: str = Form(...),
    extract_knowledge: bool = Form(False),
    db: Neo4jDatabase = Depends(get_db)
):
    """处理URL并可选地提取知识"""
    # 创建文档处理器
    document_processor = DocumentProcessor()
    
    # 处理URL
    result = await document_processor.process_url(url)
    
    if result.error:
        raise HTTPException(status_code=400, detail=f"Error processing URL: {result.error}")
    
    # 如果需要，提取知识
    entities = []
    relationships = []
    if extract_knowledge:
        try:
            # 创建知识抽取器
            extractor = SpacyNERExtractor(db)
            
            # 提取实体
            entities = await extractor.extract_entities(result.document, result.text_content)
            
            # 提取关系
            relationships = await extractor.extract_relationships(result.document, entities, result.text_content)
            
            # 创建溯源记录
            await extractor.create_knowledge_traces(result.document, entities, relationships, result.text_content)
        except Exception as e:
            print(f"Error during knowledge extraction: {e}")
            # 继续处理，即使知识提取失败
    
    return {
        "document": result.document,
        "extracted_entities": len(entities),
        "extracted_relationships": len(relationships),
        "message": "URL processed successfully"
    }


@router.get("/", response_model=List[SourceDocument])
async def read_documents(
    skip: int = 0,
    limit: int = 100,
    document_type: Optional[str] = None,
    title: Optional[str] = Query(None, description="文档标题（支持模糊匹配）"),
    db: Neo4jDatabase = Depends(get_db)
):
    """获取文档列表，支持分页和过滤"""
    # 这里需要实现文档查询逻辑
    # 为简化示例，返回空列表
    return []


@router.get("/{document_id}", response_model=SourceDocument)
async def read_document(
    document_id: UUID,
    db: Neo4jDatabase = Depends(get_db)
):
    """获取指定ID的文档"""
    # 这里需要实现文档获取逻辑
    # 为简化示例，抛出404错误
    raise HTTPException(status_code=404, detail="Document not found")


@router.delete("/{document_id}", response_model=bool)
async def delete_document(
    document_id: UUID,
    db: Neo4jDatabase = Depends(get_db)
):
    """删除文档"""
    # 这里需要实现文档删除逻辑
    # 为简化示例，返回成功
    return True


@router.get("/{document_id}/preview")
async def preview_document(
    document_id: UUID,
    db: Neo4jDatabase = Depends(get_db)
):
    """预览文档内容"""
    # 这里需要实现文档预览逻辑
    # 为简化示例，返回简单内容
    return {"content": "Document preview content would be displayed here"}


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    db: Neo4jDatabase = Depends(get_db)
):
    """下载文档"""
    # 这里需要实现文档下载逻辑
    # 为简化示例，抛出404错误
    raise HTTPException(status_code=404, detail="Document not found")


@router.post("/{document_id}/extract", response_model=dict)
async def extract_knowledge(
    document_id: UUID,
    db: Neo4jDatabase = Depends(get_db)
):
    """从文档提取知识"""
    # 这里需要实现知识提取逻辑
    # 为简化示例，返回简单结果
    return {
        "document_id": str(document_id),
        "extracted_entities": 0,
        "extracted_relationships": 0,
        "message": "Knowledge extraction would be performed here"
    }


@router.get("/{document_id}/export")
async def export_document(
    document_id: UUID,
    db: Neo4jDatabase = Depends(get_db)
):
    """导出文档及其关联知识"""
    # 这里需要实现文档导出逻辑
    # 为简化示例，返回简单内容
    return {
        "document_id": str(document_id),
        "metadata": {},
        "knowledge": {
            "entities": [],
            "relationships": []
        }
    }