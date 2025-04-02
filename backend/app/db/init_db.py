from sqlalchemy.orm import Session
from .sqlite_db import engine, Base, SessionLocal
from .models import EntityType

def init_db():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)
    
    # 初始化实体类型
    db = SessionLocal()
    try:
        # 检查是否已有数据
        if db.query(EntityType).count() == 0:
            # 添加默认实体类型
            default_types = [
                {"type_code": "person", "type_name": "人物", "icon": "fa-user", "color": "#ff7f0e"},
                {"type_code": "organization", "type_name": "组织", "icon": "fa-building", "color": "#1f77b4"},
                {"type_code": "location", "type_name": "地点", "icon": "fa-map-marker", "color": "#2ca02c"},
                {"type_code": "concept", "type_name": "概念", "icon": "fa-lightbulb", "color": "#d62728"},
                {"type_code": "time", "type_name": "时间", "icon": "fa-clock", "color": "#9467bd"},
                {"type_code": "event", "type_name": "事件", "icon": "fa-calendar", "color": "#8c564b"}
            ]
            
            for type_data in default_types:
                entity_type = EntityType(**type_data)
                db.add(entity_type)
            
            db.commit()
    finally:
        db.close()