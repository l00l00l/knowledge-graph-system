# app/services/document_index.py

from typing import List, Dict, Any, Optional
import aiofiles
import json
import os
import re
from uuid import UUID
import asyncio
import sqlite3
import aiosqlite
from pathlib import Path

class DocumentIndex:
    """文档索引与检索服务"""
    
    def __init__(self, index_db_path: str):
        self.index_db_path = index_db_path
        self.initialized = False
    
    async def initialize(self):
        """初始化索引数据库"""
        # 确保目录存在
        os.makedirs(os.path.dirname(self.index_db_path), exist_ok=True)
        
        async with aiosqlite.connect(self.index_db_path) as db:
            # 创建文档表
            await db.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                type TEXT NOT NULL,
                file_path TEXT,
                url TEXT,
                archived_path TEXT,
                content_hash TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            ''')
            
            # 创建全文索引表
            await db.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS document_fts USING fts5(
                id,
                title,
                content,
                metadata,
                tokenize='porter unicode61'
            )
            ''')
            
            # 创建文档元数据表
            await db.execute('''
            CREATE TABLE IF NOT EXISTS document_metadata (
                document_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                PRIMARY KEY (document_id, key),
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
            ''')
            
            await db.commit()
        
        self.initialized = True
    
    async def add_document(self, document_id: str, title: str, doc_type: str, 
                          content: str, metadata: Dict[str, Any], 
                          file_path: Optional[str] = None,
                          url: Optional[str] = None,
                          archived_path: Optional[str] = None,
                          content_hash: Optional[str] = None) -> bool:
        """添加文档到索引"""
        if not self.initialized:
            await self.initialize()
        
        try:
            async with aiosqlite.connect(self.index_db_path) as db:
                # 插入文档基本信息
                now = datetime.utcnow().isoformat()
                await db.execute('''
                INSERT INTO documents 
                (id, title, type, file_path, url, archived_path, content_hash, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (document_id, title, doc_type, file_path, url, archived_path, content_hash, now, now))
                
                # 插入文档内容到全文索引
                metadata_json = json.dumps(metadata)
                await db.execute('''
                INSERT INTO document_fts (id, title, content, metadata)
                VALUES (?, ?, ?, ?)
                ''', (document_id, title, content, metadata_json))
                
                # 插入结构化元数据
                for key, value in self._flatten_metadata(metadata):
                    await db.execute('''
                    INSERT INTO document_metadata (document_id, key, value)
                    VALUES (?, ?, ?)
                    ''', (document_id, key, str(value)))
                
                await db.commit()
                return True
        except Exception as e:
            print(f"Error indexing document: {e}")
            return False
    
    async def search(self, query: str, filters: Dict[str, Any] = None, 
                    limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """搜索文档索引"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # 构建基本搜索查询
            search_query = query.strip()
            base_query = f'''
            SELECT d.id, d.title, d.type, d.file_path, d.url, d.archived_path, 
                  d.content_hash, d.created_at, d.updated_at, fts.content
            FROM document_fts AS fts
            JOIN documents AS d ON fts.id = d.id
            WHERE document_fts MATCH ?
            '''
            
            params = [search_query]
            
            # 添加过滤条件
            filter_conditions = []
            if filters:
                for key, value in filters.items():
                    if key in ['type', 'title']:
                        filter_conditions.append(f"d.{key} = ?")
                        params.append(value)
                    else:
                        # 处理元数据过滤
                        filter_conditions.append('''
                        EXISTS (
                            SELECT 1 FROM document_metadata 
                            WHERE document_id = d.id AND key = ? AND value = ?
                        )
                        ''')
                        params.append(key)
                        params.append(str(value))
            
            if filter_conditions:
                base_query += " AND " + " AND ".join(filter_conditions)
            
            # 添加分页
            base_query += " ORDER BY fts.rank LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            # 执行查询
            async with aiosqlite.connect(self.index_db_path) as db:
                db.row_factory = sqlite3.Row
                cursor = await db.execute(base_query, params)
                rows = await cursor.fetchall()
                
                results = []
                for row in rows:
                    # 获取文档元数据
                    meta_cursor = await db.execute('''
                    SELECT key, value FROM document_metadata WHERE document_id = ?
                    ''', (row['id'],))
                    metadata = {k: v for k, v in await meta_cursor.fetchall()}
                    
                    # 构建结果
                    result = dict(row)
                    result['metadata'] = metadata
                    
                    # 提取匹配上下文
                    content = row['content']
                    context = self._extract_context(content, search_query, 150)
                    result['context'] = context
                    
                    results.append(result)
                
                return results
        
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []
    
    def _flatten_metadata(self, metadata: Dict[str, Any], prefix: str = "") -> List[tuple]:
        """将嵌套的元数据扁平化为键值对"""
        result = []
        for key, value in metadata.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                result.extend(self._flatten_metadata(value, full_key))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        result.extend(self._flatten_metadata(item, f"{full_key}.{i}"))
                    else:
                        result.append((f"{full_key}.{i}", item))
            else:
                result.append((full_key, value))
        
        return result
    
    def _extract_context(self, content: str, query: str, context_chars: int = 150) -> List[str]:
        """提取搜索词周围的文本上下文"""
        # 简单实现，实际系统可能需要更复杂的匹配算法
        words = set(re.findall(r'\w+', query.lower()))
        matches = []
        
        for word in words:
            pattern = re.compile(r'(.{0,%d})(\b%s\b)(.{0,%d})' % 
                               (context_chars//2, re.escape(word), context_chars//2), 
                               re.IGNORECASE)
            
            for match in pattern.finditer(content):
                before, term, after = match.groups()
                context = f"{before}{term}{after}"
                matches.append(context.strip())
        
        return matches[:5]  # 限制返回的上下文片段数量