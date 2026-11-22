from backend.app.routers.auth import router as auth_router
from backend.app.routers.categories import router as categories_router
from backend.app.routers.tickets import router as tickets_router
from backend.app.routers.admin import router as admin_router

__all__ = [
    "auth_router",
    "categories_router",
    "tickets_router",
    "admin_router",
]
