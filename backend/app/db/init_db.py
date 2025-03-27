from .sqlite_db import engine, Base

def init_db():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)