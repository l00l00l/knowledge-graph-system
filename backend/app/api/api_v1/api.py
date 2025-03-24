# backend/app/api/api_v1/api.py
from fastapi import APIRouter

from .endpoints import entities, relationships, documents

api_router = APIRouter()

api_router.include_router(entities.router, prefix="/entities", tags=["entities"])
api_router.include_router(relationships.router, prefix="/relationships", tags=["relationships"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])