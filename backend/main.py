from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text

from config import settings
from database.session import SessionLocal
from app.core.exceptions import ViziCheckException
from app.middleware.logging import LoggingMiddleware
from app.middleware.auth import AuthenticationMiddleware
from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.profile import router as profile_router
from app.api.routes.tenants import router as tenants_router
from app.utils.logger import get_logger

# Initialize logger
logger = get_logger("main")

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Register middlewares
app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthenticationMiddleware)

# Register CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# --- Exception Handlers ---

@app.exception_handler(ViziCheckException)
async def vizicheck_exception_handler(request: Request, exc: ViziCheckException):
    """
    Global handler for custom ViziCheck business exceptions.
    Returns custom JSON error envelope.
    """
    logger.warning(f"Business Exception: {exc.message} | Status: {exc.status_code}")
    errors = exc.errors if exc.errors else [exc.message]
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "data": None,
            "errors": errors
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Global handler for Pydantic input validation failures.
    Formats loc and message to match custom JSON error envelope.
    """
    errors = []
    for error in exc.errors():
        loc = " -> ".join(str(item) for item in error.get("loc", []))
        msg = error.get("msg", "Validation error")
        errors.append(f"{loc}: {msg}")

    logger.warning(f"Validation Exception: {errors}")
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation failed",
            "data": None,
            "errors": errors
        }
    )

# --- Routes ---

# Register API v1 routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(profile_router, prefix=settings.API_V1_STR)
app.include_router(tenants_router, prefix=settings.API_V1_STR)


@app.get("/health")
def health_check():
    """
    System health check endpoint verifying database connectivity.
    """
    db_status = "healthy"
    try:
        # Verify database connectivity
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        logger.critical(f"Database connectivity check failed: {str(e)}")

    status = "healthy" if db_status == "healthy" else "degraded"
    
    return {
        "success": True,
        "message": "Service status retrieved successfully",
        "data": {
            "status": status,
            "project": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "database": db_status
        },
        "errors": None
    }

