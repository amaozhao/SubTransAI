from fastapi import APIRouter

from app.api.api_v1.endpoints import users, glossaries, translations, translate

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(glossaries.router, prefix="/glossaries", tags=["glossaries"])
api_router.include_router(translations.router, prefix="/translations", tags=["translations"])
api_router.include_router(translate.router, prefix="/translate", tags=["translate"])
