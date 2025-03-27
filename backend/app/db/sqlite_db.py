from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 确保数据目录存在
os.makedirs("./data", exist_ok=True)

# 创建SQLite数据库引擎
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/documents.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建模型基类
Base = declarative_base()

# 获取SQLite数据库会话 - 使用不同的函数名避免冲突
def get_sqlite_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()