from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from llmsync.config import settings
from llmsync.database import get_db, init_db, close_db, engine
from llmsync.services.redis_client import redis_client
from llmsync.services.minio_client import minio_client
from llmsync.routers import auth, threads, messages, files, sync, users, devices
import logging
import sys
from datetime import datetime, timezone
from pythonjsonlogger import jsonlogger

# Structured logging
logHandler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(name)s %(levelname)s %(message)s'
)
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Sentry integration (optional)
if settings.sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastAPIIntegration
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[FastAPIIntegration()],
        traces_sample_rate=0.1,
        environment="production"
    )

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="LLMSync API",
    version="0.1.0",
    description="LLM conversation sync service"
)

# Add rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    logger.info("Starting LLMSync API")
    await init_db()
    await redis_client.connect()
    await minio_client.init_bucket()

@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down LLMSync API")
    await close_db()
    await redis_client.disconnect()

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(devices.router)
app.include_router(threads.router)
app.include_router(messages.router)
app.include_router(files.router)
app.include_router(sync.router)

@app.get("/api/health")
@limiter.limit("100/minute")
async def health_check(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        # Test database connection
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

@app.get("/api/health/full")
@limiter.limit("60/minute")
async def full_health_check(request: Request, db: AsyncSession = Depends(get_db)):
    """Comprehensive health check for all services."""
    from sqlalchemy import text

    health = {
        "api": "healthy",
        "database": "unknown",
        "redis": "unknown",
        "minio": "unknown",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # Check Postgres
    try:
        await db.execute(text("SELECT 1"))
        health["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health["database"] = "unhealthy"

    # Check Redis
    try:
        await redis_client.redis.ping()
        health["redis"] = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health["redis"] = "unhealthy"

    # Check MinIO
    try:
        minio_client.client.bucket_exists(minio_client.bucket)
        health["minio"] = "healthy"
    except Exception as e:
        logger.error(f"MinIO health check failed: {e}")
        health["minio"] = "unhealthy"

    # Overall status
    all_healthy = all(v == "healthy" for k, v in health.items() if k not in ["timestamp"])
    health["status"] = "healthy" if all_healthy else "unhealthy"

    return health
