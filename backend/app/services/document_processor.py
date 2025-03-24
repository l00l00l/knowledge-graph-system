# 文件: app/services/document_processor.py
import hashlib
import os
import mimetypes
from typing import Dict, Any, Optional, List, BinaryIO
from uuid import UUID, uuid4
from datetime import datetime
import aiofiles
from pydantic import BaseModel

from app.models.documents.source_document import SourceDocument
from app.core.config import settings


class DocumentProcessorResult(BaseModel):
    """文档处理结果"""
    document: SourceDocument
    text_content: str
    metadata: Dict[str, Any]
    error: Optional[str] = None


class DocumentProcessor:
    """文档处理器 - 负责解析各类文档并提取内容"""
    
    def __init__(self, documents_dir: str = None, archives_dir: str = None):
        self.documents_dir = documents_dir or settings.DOCUMENTS_DIR
        self.archives_dir = archives_dir or settings.ARCHIVES_DIR
        os.makedirs(self.documents_dir, exist_ok=True)
        os.makedirs(self.archives_dir, exist_ok=True)
    
    async def process_file(self, file: BinaryIO, filename: str) -> DocumentProcessorResult:
        """处理上传的文件"""
        # 确定文件类型
        file_type = self._determine_file_type(filename)
        
        # 计算文件哈希，用于唯一标识
        file_content = file.read()
        file.seek(0)  # 重置文件指针
        content_hash = hashlib.sha256(file_content).hexdigest()
        
        # 保存文件
        file_id = uuid4()
        file_path = os.path.join(self.documents_dir, f"{file_id}_{filename}")
        archived_path = os.path.join(self.archives_dir, f"{file_id}_{filename}")
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        async with aiofiles.open(archived_path, 'wb') as f:
            await f.write(file_content)
        
        # 提取文本内容和元数据
        text_content, metadata = await self._extract_content_and_metadata(file_path, file_type)
        
        # 创建源文档记录
        document = SourceDocument(
            id=file_id,
            title=filename,
            type=file_type,
            content_hash=f"sha256:{content_hash}",
            file_path=file_path,
            archived_path=archived_path,
            metadata=metadata,
            accessed_at=datetime.now(),
        )
        
        return DocumentProcessorResult(
            document=document,
            text_content=text_content,
            metadata=metadata
        )
    
    async def process_url(self, url: str) -> DocumentProcessorResult:
        """处理网页URL"""
        from playwright.async_api import async_playwright
        import warcio
        from io import BytesIO
        
        # 使用Playwright抓取网页
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                await page.goto(url, wait_until="networkidle")
                title = await page.title()
                html_content = await page.content()
                
                # 提取纯文本
                text_content = await page.evaluate("document.body.innerText")
                
                # 创建WARC存档
                file_id = uuid4()
                warc_path = os.path.join(self.archives_dir, f"{file_id}_webpage.warc.gz")
                
                # 生成WARC记录
                output = BytesIO()
                writer = warcio.WARCWriter(output, gzip=True)
                
                # 添加请求记录
                request_headers = {
                    'User-Agent': 'Mozilla/5.0 Personal Knowledge Graph Archiver'
                }
                request_record = writer.create_warcinfo_record(
                    filename=warc_path,
                    info={
                        'software': 'Personal Knowledge Graph System',
                        'format': 'WARC File Format 1.1'
                    }
                )
                writer.write_record(request_record)
                
                # 添加响应记录
                response_record = writer.create_response_record(
                    uri=url,
                    record_id=str(uuid4()),
                    content_type='text/html',
                    payload=BytesIO(html_content.encode('utf-8')),
                    http_headers={
                        'Content-Type': 'text/html',
                        'Status': '200',
                    }
                )
                writer.write_record(response_record)
                
                # 保存WARC文件
                async with aiofiles.open(warc_path, 'wb') as f:
                    await f.write(output.getvalue())
                
                # 计算内容哈希
                content_hash = hashlib.sha256(html_content.encode('utf-8')).hexdigest()
                
                # 元数据提取
                metadata = {
                    'title': title,
                    'url': url,
                    'retrieved_at': datetime.now().isoformat(),
                    'archive_format': 'WARC/1.1',
                }
                
                # 创建源文档记录
                document = SourceDocument(
                    id=file_id,
                    title=title or url,
                    type='webpage',
                    content_hash=f"sha256:{content_hash}",
                    url=url,
                    archived_path=warc_path,
                    metadata=metadata,
                    accessed_at=datetime.now(),
                )
                
                return DocumentProcessorResult(
                    document=document,
                    text_content=text_content,
                    metadata=metadata
                )
            
            except Exception as e:
                return DocumentProcessorResult(
                    document=SourceDocument(
                        id=uuid4(),
                        title=url,
                        type='webpage',
                        content_hash="error",
                        url=url,
                        archived_path=None,
                        metadata={},
                    ),
                    text_content="",
                    metadata={},
                    error=str(e)
                )
            finally:
                await browser.close()
    
    def _determine_file_type(self, filename: str) -> str:
        """确定文件类型"""
        _, extension = os.path.splitext(filename)
        extension = extension.lower()
        
        if extension == '.pdf':
            return 'pdf'
        elif extension in ['.doc', '.docx']:
            return 'docx'
        elif extension == '.txt':
            return 'txt'
        elif extension in ['.csv', '.xls', '.xlsx']:
            return 'structured_data'
        elif extension in ['.json', '.xml']:
            return 'structured_data'
        else:
            # 尝试通过MIME类型确定
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type:
                if 'pdf' in mime_type:
                    return 'pdf'
                elif 'word' in mime_type:
                    return 'docx'
                elif 'text' in mime_type:
                    return 'txt'
                elif 'csv' in mime_type or 'excel' in mime_type:
                    return 'structured_data'
                elif 'json' in mime_type or 'xml' in mime_type:
                    return 'structured_data'
            
            # 默认为普通文本
            return 'txt'
    
    async def _extract_content_and_metadata(self, file_path: str, file_type: str) -> tuple[str, dict]:
        """提取文件内容和元数据"""
        text_content = ""
        metadata = {}
        
        if file_type == 'pdf':
            # 使用PyPDF2或pdfplumber提取PDF内容
            import pdfplumber
            
            with pdfplumber.open(file_path) as pdf:
                # 提取元数据
                metadata = {
                    'pages': len(pdf.pages),
                    'author': pdf.metadata.get('Author'),
                    'creator': pdf.metadata.get('Creator'),
                    'producer': pdf.metadata.get('Producer'),
                    'subject': pdf.metadata.get('Subject'),
                    'title': pdf.metadata.get('Title'),
                }
                
                # 提取文本内容
                text_parts = []
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    text_parts.append(text)
                
                text_content = "\n\n".join(text_parts)
        
        elif file_type == 'docx':
            # 使用python-docx提取Word文档内容
            import docx
            
            doc = docx.Document(file_path)
            
            # 提取元数据
            metadata = {
                'author': doc.core_properties.author,
                'created': doc.core_properties.created.isoformat() if doc.core_properties.created else None,
                'last_modified_by': doc.core_properties.last_modified_by,
                'modified': doc.core_properties.modified.isoformat() if doc.core_properties.modified else None,
                'title': doc.core_properties.title,
                'paragraphs': len(doc.paragraphs),
            }
            
            # 提取文本内容
            text_content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        
        elif file_type == 'txt':
            # 直接读取文本文件
            async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                text_content = await f.read()
            
            metadata = {
                'size': os.path.getsize(file_path),
                'encoding': 'utf-8',
            }
        
        elif file_type == 'structured_data':
            # 处理CSV、JSON等结构化数据
            import pandas as pd
            import json
            
            _, extension = os.path.splitext(file_path)
            extension = extension.lower()
            
            if extension == '.csv':
                try:
                    df = pd.read_csv(file_path)
                    metadata = {
                        'columns': df.columns.tolist(),
                        'rows': len(df),
                        'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                    }
                    # 将CSV转换为文本形式
                    text_content = df.to_string(index=False)
                except Exception as e:
                    text_content = f"Error processing CSV: {str(e)}"
            
            elif extension == '.json':
                try:
                    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                        json_content = await f.read()
                    
                    json_data = json.loads(json_content)
                    
                    if isinstance(json_data, dict):
                        metadata = {
                            'keys': list(json_data.keys()),
                            'type': 'object',
                        }
                    elif isinstance(json_data, list):
                        metadata = {
                            'length': len(json_data),
                            'type': 'array',
                        }
                    
                    # 将JSON转换为漂亮的文本形式
                    text_content = json.dumps(json_data, indent=2, ensure_ascii=False)
                except Exception as e:
                    text_content = f"Error processing JSON: {str(e)}"
        
        return text_content, metadata
