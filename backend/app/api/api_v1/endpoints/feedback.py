# app/api/api_v1/endpoints/feedback.py

from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any, List, Optional
from uuid import UUID

from app.models.entities.entity import Entity
from app.models.relationships.relationship import Relationship
from app.db.neo4j_db import Neo4jDatabase
from app.api.deps import get_db
from app.services.knowledge_extractor import KnowledgeExtractor

router = APIRouter()


@router.post("/entity/{entity_id}/feedback", response_model=Dict[str, Any])
async def provide_entity_feedback(
    entity_id: UUID,
    feedback: Dict[str, Any] = Body(...),
    db: Neo4jDatabase = Depends(get_db)
):
    """提供实体反馈"""
    # 获取实体
    entity = await db.read(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # 处理反馈类型
    feedback_type = feedback.get("type")
    
    if feedback_type == "correction":
        # 实体属性校正
        corrected_data = feedback.get("data", {})
        
        # 创建新版本
        new_entity = Entity(
            **entity.dict(),
            id=UUID(entity_id),
            version=entity.version + 1,
            previous_version=entity.id
        )
        
        # 应用修正
        for key, value in corrected_data.items():
            if hasattr(new_entity, key):
                setattr(new_entity, key, value)
        
        # 记录用户反馈
        if not new_entity.properties:
            new_entity.properties = {}
        
        new_entity.properties["user_feedback"] = {
            "timestamp": feedback.get("timestamp"),
            "type": feedback_type,
            "confidence": feedback.get("confidence", 1.0)
        }
        
        # 更新实体
        updated_entity = await db.update(entity_id, new_entity)
        return {"status": "success", "entity": updated_entity}
    
    elif feedback_type == "removal":
        # 删除错误实体
        success = await db.delete(entity_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to remove entity")
        
        return {"status": "success", "message": "Entity removed"}
    
    elif feedback_type == "confirmation":
        # 确认实体正确
        new_entity = Entity(
            **entity.dict(),
            confidence=max(entity.confidence or 0, 0.95)  # 提高置信度
        )
        
        if not new_entity.properties:
            new_entity.properties = {}
        
        new_entity.properties["user_confirmed"] = True
        new_entity.properties["confirmation_timestamp"] = feedback.get("timestamp")
        
        # 更新实体
        updated_entity = await db.update(entity_id, new_entity)
        return {"status": "success", "entity": updated_entity}
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported feedback type: {feedback_type}")


@router.post("/relationship/{relationship_id}/feedback", response_model=Dict[str, Any])
async def provide_relationship_feedback(
    relationship_id: UUID,
    feedback: Dict[str, Any] = Body(...),
    db: Neo4jDatabase = Depends(get_db)
):
    """提供关系反馈"""
    # 获取关系
    relationship = await db.read(relationship_id)
    if not relationship:
        raise HTTPException(status_code=404, detail="Relationship not found")
    
    # 处理反馈类型
    feedback_type = feedback.get("type")
    
    # 类似实体反馈的处理逻辑
    # 省略类似实现...
    
    return {"status": "success"}


@router.post("/batch-feedback", response_model=Dict[str, Any])
async def provide_batch_feedback(
    feedback_items: List[Dict[str, Any]] = Body(...),
    db: Neo4jDatabase = Depends(get_db)
):
    """批量提供反馈"""
    results = {
        "success_count": 0,
        "failure_count": 0,
        "failures": []
    }
    
    for item in feedback_items:
        try:
            item_type = item.get("item_type")
            item_id = UUID(item.get("item_id"))
            feedback_data = item.get("feedback")
            
            if item_type == "entity":
                await provide_entity_feedback(item_id, feedback_data, db)
                results["success_count"] += 1
            elif item_type == "relationship":
                await provide_relationship_feedback(item_id, feedback_data, db)
                results["success_count"] += 1
            else:
                results["failure_count"] += 1
                results["failures"].append({
                    "item": item,
                    "error": f"Unsupported item type: {item_type}"
                })
        except Exception as e:
            results["failure_count"] += 1
            results["failures"].append({
                "item": item,
                "error": str(e)
            })
    
    return results


@router.get("/pending-reviews", response_model=Dict[str, Any])
async def get_pending_reviews(
    confidence_threshold: float = 0.7,
    limit: int = 20,
    db: Neo4jDatabase = Depends(get_db)
):
    """获取待审核的低置信度知识项"""
    # 查询低置信度实体
    low_confidence_entities = await db.find({
        "confidence_lt": confidence_threshold,
        "properties.user_confirmed_ne": True
    })
    
    # 查询低置信度关系
    low_confidence_relationships = await db.find({
        "confidence_lt": confidence_threshold,
        "properties.user_confirmed_ne": True
    })
    
    # 按置信度排序
    entities = sorted(low_confidence_entities, key=lambda e: e.confidence or 0)
    relationships = sorted(low_confidence_relationships, key=lambda r: r.confidence or 0)
    
    return {
        "entities": entities[:limit//2],
        "relationships": relationships[:limit//2],
        "total_pending": len(entities) + len(relationships)
    }