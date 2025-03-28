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
import aiofiles  # 确保在文件顶部导入这个库
from sqlalchemy.orm import Session
from app.db.sqlite_db import get_sqlite_db
from app.db.models import Document
from app.db.init_db import init_db
from fastapi.responses import FileResponse

# 修正导入路径
from app.services.knowledge_extractor import SpacyNERExtractor

from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, Optional

init_db()

class DocumentResponse(BaseModel):
    """文档响应模型"""
    id: str
    title: str
    type: str
    content_hash: str
    file_path: Optional[str] = None
    url: Optional[str] = None
    archived_path: Optional[str] = None
    metadata: Dict[str, Any] = {}
    accessed_at: datetime
    created_at: datetime
    updated_at: datetime

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

# Enhanced upload endpoint with better error handling

@router.post("/upload", response_model=Dict[str, Any])
async def upload_document(
    file: UploadFile = File(...),
    extract_knowledge: bool = Form(False),
    sqlite_db: Session = Depends(get_sqlite_db),
    neo4j_db: Neo4jDatabase = Depends(get_db)
):
    """上传文档并可选地提取知识"""
    try:
        # 创建文档处理器
        document_processor = DocumentProcessor()
        
        # 处理文档
        try:
            result = await document_processor.process_file(file.file, file.filename)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error processing document: {str(e)}")
        
        if result.error:
            raise HTTPException(status_code=400, detail=f"Error processing document: {result.error}")
        
        # 确保metadata是有效的JSON
        metadata_json = "{}"
        if result.document.metadata:
            try:
                # Make sure it's serializable
                metadata_json = json.dumps(result.document.metadata)
                # Verify it can be parsed back
                json.loads(metadata_json)
                print(f"Valid metadata JSON created: {metadata_json[:100]}...")
            except Exception as e:
                print(f"Error serializing metadata to JSON: {e}")
                metadata_json = "{}"
        
        # 将文档存入SQLite数据库
        doc_model = Document(
            id=str(result.document.id),
            title=result.document.title,
            type=result.document.type,
            content_hash=result.document.content_hash,
            file_path=result.document.file_path,
            url=result.document.url,
            archived_path=result.document.archived_path,
            doc_metadata=metadata_json  # 使用验证过的JSON
        )
        
        # 添加到数据库
        sqlite_db.add(doc_model)
        sqlite_db.commit()
        sqlite_db.refresh(doc_model)
        
        print(f"Document saved to SQLite with ID: {doc_model.id}")
        
        # 验证存储的JSON
        verification = sqlite_db.query(Document).filter(Document.id == doc_model.id).first()
        if verification:
            print(f"Successfully verified document in database: {verification.title}")
            print(f"Stored doc_metadata: {verification.doc_metadata[:100]}...")
        else:
            print(f"WARNING: Could not verify document {doc_model.id} in database")
        
        # 如果需要，提取知识
        entities = []
        relationships = []
        extract_error = None
        
        if extract_knowledge:
            try:
                # 创建知识抽取器 - 使用Neo4j
                extractor = SpacyNERExtractor(neo4j_db)
                
                # 提取实体
                entities = await extractor.extract_entities(result.document, result.text_content)
                
                # 提取关系
                if len(entities) >= 2:
                    relationships = await extractor.extract_relationships(result.document, entities, result.text_content)
                    
                    # 创建溯源记录
                    await extractor.create_knowledge_traces(result.document, entities, relationships, result.text_content)
                
            except Exception as e:
                extract_error = str(e)
                print(f"Error during knowledge extraction: {e}")
        
        # 将文档转为字典以便序列化
        document_dict = doc_model.to_dict()
        
        return {
            "document": document_dict,
            "extracted_entities": len(entities),
            "extracted_relationships": len(relationships),
            "extraction_error": extract_error,
            "message": "Document processed successfully" + (
                " but knowledge extraction failed: " + extract_error if extract_error else ""
            )
        }
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Capture any other unexpected errors
        import traceback
        traceback.print_exc()
        print(f"Unexpected error in upload_document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


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
    sqlite_db: Session = Depends(get_sqlite_db)
):
    """获取文档列表，支持分页和过滤"""
    try:
        # 查询SQLite数据库
        query = sqlite_db.query(Document)
        
        # 应用过滤条件
        if document_type:
            query = query.filter(Document.type == document_type)
        
        if title:
            query = query.filter(Document.title.like(f"%{title}%"))
        
        # 按创建时间降序排序
        query = query.order_by(Document.created_at.desc())
        
        # 应用分页
        query = query.offset(skip).limit(limit)
        
        # 获取结果
        documents = query.all()
        print(f"Retrieved {len(documents)} documents from SQLite database")
        
        # 转换为字典列表返回
        result = [doc.to_dict() for doc in documents]
        print(f"Converted {len(result)} documents to dictionary format")
        
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error retrieving documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")

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

@router.get("/{document_id}/preview")
async def preview_document(
    document_id: str,
    sqlite_db: Session = Depends(get_sqlite_db)
):
    """预览文档内容"""
    try:
        # 从SQLite获取文档
        document = sqlite_db.query(Document).filter(Document.id == document_id).first()
        
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = document.file_path
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Document file not found")
        
        # 读取文件内容
        content = ""
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                binary_content = await f.read()
                
            # 尝试将内容解码为文本
            try:
                content = binary_content.decode('utf-8', errors='replace')
            except UnicodeDecodeError:
                content = f"[Binary content - {len(binary_content)} bytes]"
                
        except Exception as e:
            content = f"Error reading file: {str(e)}"
        
        return {
            "title": document.title,
            "type": document.type,
            "content": content,
            "preview_available": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error previewing document: {str(e)}")


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    sqlite_db: Session = Depends(get_sqlite_db)
):
    """下载文档"""
    try:
        # 从SQLite获取文档
        document = sqlite_db.query(Document).filter(Document.id == document_id).first()
        
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = document.file_path
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Document file not found")
        
        # 获取文件名
        filename = os.path.basename(file_path)
        
        # 使用 FileResponse 处理文件下载
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading document: {str(e)}")

@router.delete("/{document_id}", response_model=bool)
async def delete_document(
    document_id: str,
    sqlite_db: Session = Depends(get_sqlite_db)
):
    """删除文档"""
    try:
        # 从SQLite获取文档
        document = sqlite_db.query(Document).filter(Document.id == document_id).first()
        
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # 尝试删除物理文件
        try:
            if document.file_path and os.path.exists(document.file_path):
                os.remove(document.file_path)
            
            if document.archived_path and os.path.exists(document.archived_path):
                os.remove(document.archived_path)
        except Exception as file_error:
            # 记录错误但继续，因为数据库记录已删除
            print(f"Warning: Failed to delete physical file: {str(file_error)}")
        
        # 从数据库删除记录
        sqlite_db.delete(document)
        sqlite_db.commit()
        
        return True
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

# 替换 documents.py 中的 preview_document 函数

@router.get("/{document_id}/preview")
async def preview_document(
    document_id: UUID,
    db: Neo4jDatabase = Depends(get_db)
):
    """预览文档内容"""
    try:
        # 在 mock_documents 中查找
        for doc in mock_documents:
            if doc.id == document_id:
                file_path = doc.file_path
                if not file_path or not os.path.exists(file_path):
                    raise HTTPException(status_code=404, detail="Document file not found")
                
                # 读取文件内容
                content = ""
                try:
                    async with aiofiles.open(file_path, 'rb') as f:
                        binary_content = await f.read()
                        
                    # 尝试将内容解码为文本
                    try:
                        content = binary_content.decode('utf-8', errors='replace')
                    except UnicodeDecodeError:
                        content = f"[Binary content - {len(binary_content)} bytes]"
                        
                except Exception as e:
                    content = f"Error reading file: {str(e)}"
                
                return {
                    "title": doc.title,
                    "type": doc.type,
                    "content": content,
                    "preview_available": True
                }
        
        raise HTTPException(status_code=404, detail="Document not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error previewing document: {str(e)}")


# 替换 documents.py 中的 download_document 函数

@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    db: Neo4jDatabase = Depends(get_db)
):
    """下载文档"""
    try:
        # 在 mock_documents 中查找
        for doc in mock_documents:
            if doc.id == document_id:
                file_path = doc.file_path
                if not file_path or not os.path.exists(file_path):
                    raise HTTPException(status_code=404, detail="Document file not found")
                
                filename = os.path.basename(file_path)
                
                # 使用 FileResponse 处理文件下载
                from fastapi.responses import FileResponse
                return FileResponse(
                    path=file_path,
                    filename=filename,
                    media_type="application/octet-stream"
                )
        
        raise HTTPException(status_code=404, detail="Document not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading document: {str(e)}")


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