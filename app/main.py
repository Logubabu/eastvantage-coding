import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import models
from app.config import settings
from app.database import engine
from app.logging_config import setup_logging
from app.routers import addresses

logger = logging.getLogger("app.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for application startup and shutdown."""
    # 1. Setup application logging
    setup_logging()
    logger.info("Initializing Address Book application...")
    
    # 2. Automatically create database tables (for development/production ease)
    try:
        logger.info("Verifying database schema...")
        models.Base.metadata.create_all(bind=engine)
        logger.info("Database schema verified.")
    except Exception as e:
        logger.error("Failed to initialize database: %s", str(e), exc_info=True)
        raise e
        
    yield
    
    logger.info("Shutting down Address Book application...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="A FastAPI-based Address Book application with SQLite persistence, coordinates validation, and optimized distance-based search.",
    lifespan=lifespan
)

# Register routers
app.include_router(addresses.router, prefix=settings.API_V1_STR)

# Global Exception Handlers for structured responses and logging

from fastapi.exception_handlers import request_validation_exception_handler

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log validation errors and return structured 422 JSON."""
    logger.warning("Validation error on request path %s: %s", request.url.path, str(exc))
    return await request_validation_exception_handler(request, exc)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Log HTTP exceptions and return structured JSON."""
    logger.info("HTTP exception on path %s: status=%d detail=%s", request.url.path, exc.status_code, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Intercept and log unexpected backend exceptions, preventing stack traces from leaking."""
    logger.error("Unhandled exception on path %s: %s", request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact the administrator."}
    )

@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root path to interactive Swagger documentation."""
    return RedirectResponse(url="/docs")
