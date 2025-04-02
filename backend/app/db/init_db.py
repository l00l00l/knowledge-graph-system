from sqlalchemy.orm import Session
from .sqlite_db import engine, Base, SessionLocal
from .models import EntityType, RelationshipType

def init_db():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)
    
    # 初始化实体和关系类型
    db = SessionLocal()
    try:
        # 检查实体类型是否已有数据
        if db.query(EntityType).count() == 0:
            # 添加默认实体类型
            entity_types = [
                # 基础类型
                {"type_code": "concept", "type_name": "概念", "category": "基础类型", "icon": "fa-lightbulb", "color": "#d62728"},
                {"type_code": "person", "type_name": "人物", "category": "基础类型", "icon": "fa-user", "color": "#ff7f0e"},
                {"type_code": "organization", "type_name": "组织", "category": "基础类型", "icon": "fa-building", "color": "#1f77b4"},
                {"type_code": "location", "type_name": "地点", "category": "基础类型", "icon": "fa-map-marker", "color": "#2ca02c"},
                {"type_code": "time", "type_name": "时间", "category": "基础类型", "icon": "fa-clock", "color": "#9467bd"},
                {"type_code": "event", "type_name": "事件", "category": "基础类型", "icon": "fa-calendar", "color": "#8c564b"},
                
                # 领域类型
                {"type_code": "technology", "type_name": "技术", "category": "领域类型", "icon": "fa-microchip", "color": "#e377c2"},
                {"type_code": "theory", "type_name": "理论", "category": "领域类型", "icon": "fa-book", "color": "#7f7f7f"},
                {"type_code": "method", "type_name": "方法", "category": "领域类型", "icon": "fa-cogs", "color": "#bcbd22"},
                {"type_code": "problem", "type_name": "问题", "category": "领域类型", "icon": "fa-question-circle", "color": "#17becf"},
                {"type_code": "tool", "type_name": "工具", "category": "领域类型", "icon": "fa-wrench", "color": "#9edae5"},
                {"type_code": "solution", "type_name": "解决方案", "category": "领域类型", "icon": "fa-check-circle", "color": "#ffbb78"},
                
                # 个人类型
                {"type_code": "note", "type_name": "笔记", "category": "个人类型", "icon": "fa-sticky-note", "color": "#aec7e8"},
                {"type_code": "question", "type_name": "问题", "category": "个人类型", "icon": "fa-question", "color": "#ffbb78"},
                {"type_code": "idea", "type_name": "想法", "category": "个人类型", "icon": "fa-lightbulb", "color": "#98df8a"},
                {"type_code": "goal", "type_name": "目标", "category": "个人类型", "icon": "fa-bullseye", "color": "#ff9896"},
                {"type_code": "plan", "type_name": "计划", "category": "个人类型", "icon": "fa-tasks", "color": "#c5b0d5"}
            ]
            
            for entity_type in entity_types:
                db.add(EntityType(**entity_type))
        
        # 检查关系类型是否已有数据
        if db.query(RelationshipType).count() == 0:
            # 添加默认关系类型
            relationship_types = [
                # 基础类型
                {"type_code": "is_a", "type_name": "是一种", "category": "基础类型", "icon": "fa-sitemap", "color": "#666666"},
                {"type_code": "part_of", "type_name": "是部分", "category": "基础类型", "icon": "fa-puzzle-piece", "color": "#666666"},
                {"type_code": "attribute_of", "type_name": "是属性", "category": "基础类型", "icon": "fa-tag", "color": "#666666"},
                {"type_code": "instance_of", "type_name": "是实例", "category": "基础类型", "icon": "fa-copy", "color": "#666666"},
                
                # 领域类型
                {"type_code": "causes", "type_name": "导致", "category": "领域类型", "icon": "fa-arrow-right", "color": "#666666"},
                {"type_code": "influences", "type_name": "影响", "category": "领域类型", "icon": "fa-exchange-alt", "color": "#666666"},
                {"type_code": "depends_on", "type_name": "依赖于", "category": "领域类型", "icon": "fa-link", "color": "#666666"},
                {"type_code": "contradicts", "type_name": "矛盾于", "category": "领域类型", "icon": "fa-not-equal", "color": "#666666"},
                
                # 个人类型
                {"type_code": "similar_to", "type_name": "类似于", "category": "个人类型", "icon": "fa-equals", "color": "#666666"},
                {"type_code": "reminds_of", "type_name": "提醒我", "category": "个人类型", "icon": "fa-bell", "color": "#666666"},
                {"type_code": "inspires", "type_name": "启发", "category": "个人类型", "icon": "fa-lightbulb", "color": "#666666"},
                {"type_code": "confuses", "type_name": "困惑", "category": "个人类型", "icon": "fa-question-circle", "color": "#666666"}
            ]
            
            for rel_type in relationship_types:
                db.add(RelationshipType(**rel_type))
                
            db.commit()
    except Exception as e:
        print(f"初始化类型数据失败: {e}")
        db.rollback()
    finally:
        db.close()