# app/services/version_control.py

from typing import Dict, Any, List, Optional, Union, TypeVar, Generic
from uuid import UUID
import json
import datetime
from fastapi import HTTPException

from app.db.neo4j_enhanced import Neo4jEnhanced
from app.models.core.base_model import VersionMixin
from app.core.logger import logger

T = TypeVar('T', bound=VersionMixin)

class VersionControl(Generic[T]):
    """版本控制服务，管理实体和关系的版本历史"""
    
    def __init__(self, db: Neo4jEnhanced):
        self.db = db
    
    async def create_version(self, old_obj: T, new_obj: T) -> T:
        """创建新版本，保存版本关系"""
        # 确保新对象引用旧对象
        new_obj.previous_version = old_obj.id
        new_obj.version = old_obj.version + 1
        
        # 创建新版本实体/关系
        cypher_query = """
        MATCH (old {id: $old_id})
        CREATE (new:Version {id: $new_id, version: $version, created_at: $created_at})
        CREATE (new)-[:PREVIOUS_VERSION]->(old)
        RETURN new
        """
        
        params = {
            "old_id": str(old_obj.id),
            "new_id": str(new_obj.id),
            "version": new_obj.version,
            "created_at": datetime.datetime.now().isoformat()
        }
        
        try:
            await self.db.execute_write_query(cypher_query, params)
            return new_obj
        except Exception as e:
            logger.error(f"Failed to create version: {e}")
            raise HTTPException(status_code=500, detail=f"Version creation failed: {e}")
    
    async def get_version_history(self, obj_id: UUID) -> List[Dict[str, Any]]:
        """获取对象的完整版本历史"""
        cypher_query = """
        MATCH (current {id: $id})
        OPTIONAL MATCH path = (current)-[:PREVIOUS_VERSION*]->(previous)
        RETURN nodes(path) as versions
        """
        
        params = {"id": str(obj_id)}
        
        try:
            results = await self.db.execute_read_query(cypher_query, params)
            if not results or not results[0]:
                return []
                
            # 处理结果，按版本号排序
            versions = []
            for version_nodes in results:
                for node in version_nodes:
                    if node and isinstance(node, dict):
                        versions.append(node)
            
            # 按版本号降序排序
            return sorted(versions, key=lambda v: v.get('version', 0), reverse=True)
        except Exception as e:
            logger.error(f"Failed to get version history: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve version history: {e}")
    
    async def revert_to_version(self, obj_id: UUID, target_version: int) -> T:
        """将对象恢复到指定版本"""
        # 获取目标版本
        cypher_query = """
        MATCH (n {id: $obj_id, version: $target_version})
        RETURN n
        """
        
        params = {
            "obj_id": str(obj_id),
            "target_version": target_version
        }
        
        try:
            results = await self.db.execute_read_query(cypher_query, params)
            if not results or not results[0]:
                raise HTTPException(status_code=404, detail=f"Version {target_version} not found")
                
            target_obj = results[0]
            
            # 创建新版本，基于目标版本
            # 这里需要根据实际模型类型进行处理
            # 省略实现...
            
            return target_obj
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Failed to revert to version: {e}")
            raise HTTPException(status_code=500, detail=f"Version revert failed: {e}")
    
    async def compare_versions(self, id1: UUID, id2: UUID) -> Dict[str, Any]:
        """比较两个版本之间的差异"""
        # 获取两个版本的完整数据
        cypher_query = """
        MATCH (n {id: $id})
        RETURN n
        """
        
        try:
            results1 = await self.db.execute_read_query(cypher_query, {"id": str(id1)})
            results2 = await self.db.execute_read_query(cypher_query, {"id": str(id2)})
            
            if not results1 or not results2:
                raise HTTPException(status_code=404, detail="One or both versions not found")
                
            obj1 = results1[0]
            obj2 = results2[0]
            
            # 计算差异
            diff = self._compute_diff(obj1, obj2)
            return diff
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Failed to compare versions: {e}")
            raise HTTPException(status_code=500, detail=f"Version comparison failed: {e}")
    
    def _compute_diff(self, obj1: Dict[str, Any], obj2: Dict[str, Any]) -> Dict[str, Any]:
        """计算两个对象之间的差异"""
        diff = {
            "added": {},
            "removed": {},
            "changed": {}
        }
        
        # 计算添加的键
        for key, value in obj2.items():
            if key not in obj1:
                diff["added"][key] = value
        
        # 计算删除的键
        for key, value in obj1.items():
            if key not in obj2:
                diff["removed"][key] = value
        
        # 计算更改的键
        for key, value in obj1.items():
            if key in obj2 and obj2[key] != value:
                diff["changed"][key] = {
                    "from": value,
                    "to": obj2[key]
                }
        
        return diff