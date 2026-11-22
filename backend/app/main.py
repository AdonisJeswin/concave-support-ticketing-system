from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database import init_db
from backend.app.routers import auth_router, categories_router, tickets_router, admin_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and triggers
    init_db()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend REST API for Concave Insights Support Ticketing System (Market Research SLAs & Continuous Escalation)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(tickets_router)
app.include_router(admin_router)

@app.get("/", tags=["Health"])
def root():
    return {
        "name": settings.APP_NAME,
        "status": "online",
        "version": "1.0.0",
        "docs_url": "/docs"
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
