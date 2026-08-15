from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.core.config import settings
from src.core.db.database import init_db
from src.api.routes import webhooks, audits, repositories, metrics


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="Enterprise Autonomous Code Audit & Self-Healing Engineering Platform API",
    lifespan=lifespan
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "environment": settings.ENV,
        "use_local_vector_store": settings.USE_LOCAL_VECTOR_STORE or not bool(settings.PINECONE_API_KEY)
    }


# Include Routes
app.include_router(webhooks.router, prefix="/api/v1")
app.include_router(audits.router, prefix="/api/v1")
app.include_router(repositories.router, prefix="/api/v1")
app.include_router(metrics.router, prefix="/api/v1")
