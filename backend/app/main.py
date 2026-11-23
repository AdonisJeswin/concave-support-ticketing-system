import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database import init_db, SessionLocal
from backend.app.routers import auth_router, categories_router, tickets_router, admin_router
from backend.app.services.sla_service import run_periodic_maintenance

async def periodic_maintenance_worker(interval_seconds: int = 60):
    """
    Lightweight background task running every 60 seconds:
    - Escalates non-paused, overdue active tickets (due_at <= now)
    - Auto-closes RESOLVED tickets whose resolved_at exceeds auto_close_days
    Shielded with try/except and safe DB session disposal.
    """
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            db = SessionLocal()
            try:
                run_periodic_maintenance(db)
            finally:
                db.close()
        except asyncio.CancelledError:
            break
        except Exception:
            # Shield background loop from unexpected errors
            pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and triggers
    init_db()

    # Start periodic 60-second background maintenance task
    maintenance_task = asyncio.create_task(periodic_maintenance_worker(interval_seconds=60))
    
    yield

    # Graceful shutdown of background task
    maintenance_task.cancel()
    try:
        await maintenance_task
    except asyncio.CancelledError:
        pass

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
