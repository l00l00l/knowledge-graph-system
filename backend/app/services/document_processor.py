# app/services/document_processor.py 增强版实现

import fitz  # PyMuPDF for advanced PDF handling
import docx
import chardet
from typing import Tuple, Dict, Any, BinaryIO
import os
import aiofiles
import hashlib
from datetime import datetime

class DocumentProcessor:
    """增强版文档处理器，支持多格式文档解析与结构保留"""
    
    async def _extract_content_and_metadata(self, file_path: str, file_type: str) -> Tuple[str, Dict[str, Any]]:
        """提取文件内容和元数据"""
        if file_type == 'pdf':
            return await self._process_pdf(file_path)
        elif file_type in ['docx', 'doc']:
            return await self._process_word(file_path)
        elif file_type == 'txt':
            return await self._process_text(file_path)
        else:
            return "", {"error": f"Unsupported file type: {file_type}"}
    
    async def _process_pdf(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """处理PDF文件，提取文本和结构信息"""
        doc = fitz.open(file_path)
        
        # 提取元数据
        metadata = {
            'title': doc.metadata.get('title', ''),
            'author': doc.metadata.get('author', ''),
            'subject': doc.metadata.get('subject', ''),
            'keywords': doc.metadata.get('keywords', ''),
            'creator': doc.metadata.get('creator', ''),
            'producer': doc.metadata.get('producer', ''),
            'creation_date': doc.metadata.get('creationDate', ''),
            'modification_date': doc.metadata.get('modDate', ''),
            'page_count': len(doc),
            'file_size': os.path.getsize(file_path),
        }
        
        # 提取结构化文本
        text_blocks = []
        toc = doc.get_toc()  # 获取目录结构
        
        # 处理每一页，保留段落和布局信息
        for page_num, page in enumerate(doc):
            page_text = ""
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if block["type"] == 0:  # 文本块
                    for line in block["lines"]:
                        line_text = " ".join(span["text"] for span in line["spans"])
                        font_info = line["spans"][0] if line["spans"] else {}
                        
                        # 记录字体、大小等排版信息，用于判断标题或正文
                        text_info = {
                            "text": line_text,
                            "page": page_num + 1,
                            "font": font_info.get("font", ""),
                            "size": font_info.get("size", 0),
                            "position": (block["bbox"][0], block["bbox"][1]),
                            "char_offset": len(page_text)
                        }
                        
                        text_blocks.append(text_info)
                        page_text += line_text + "\n"
        
        # 合并所有文本，但保留结构信息
        full_text = "\n".join(block["text"] for block in text_blocks)
        
        # 将结构信息添加到元数据
        metadata['structure'] = {
            'toc': toc,
            'text_blocks': text_blocks,
        }
        
        return full_text, metadata
    
    async def _process_word(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """处理Word文档，提取文本和结构信息"""
        doc = docx.Document(file_path)
        
        # 提取元数据
        core_properties = doc.core_properties
        metadata = {
            'title': core_properties.title or '',
            'author': core_properties.author or '',
            'subject': core_properties.subject or '',
            'keywords': core_properties.keywords or '',
            'created': core_properties.created.isoformat() if core_properties.created else '',
            'modified': core_properties.modified.isoformat() if core_properties.modified else '',
            'paragraph_count': len(doc.paragraphs),
            'file_size': os.path.getsize(file_path),
        }
        
        # 提取结构化文本
        text_blocks = []
        full_text = ""
        
        for i, para in enumerate(doc.paragraphs):
            if para.text.strip():
                # 获取段落样式信息
                style_name = para.style.name if para.style else "Normal"
                
                # 记录段落信息，包括样式、层级等
                text_info = {
                    "text": para.text,
                    "index": i,
                    "style": style_name,
                    "level": 0 if "Heading" not in style_name else int(style_name.replace("Heading ", "")),
                    "char_offset": len(full_text)
                }
                
                text_blocks.append(text_info)
                full_text += para.text + "\n"
        
        # 将结构信息添加到元数据
        metadata['structure'] = {
            'paragraphs': text_blocks,
        }
        
        return full_text, metadata