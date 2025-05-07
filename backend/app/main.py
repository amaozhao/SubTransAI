from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid
from contextvars import ContextVar

from app.core.logging import configure_logging, get_logger

from app.api.api_v1.api import api_router
from app.core.config import settings

# Configure logging
configure_logging()

# Create request_id context variable for tracking requests across logs
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

# Get logger for this module
logger = get_logger("app.main")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    version="1.0.0",
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID middleware
@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    request_id = f"ReqID:{uuid.uuid4()}"
    # Set request_id in context var for logging
    request_id_var.set(request_id)
    
    logger.info("Request started", path=request.url.path)
    
    try:
        response = await call_next(request)
        logger.info("Request completed", status_code=response.status_code)
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as e:
        logger.error("Request failed", error=str(e))
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
        )

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
