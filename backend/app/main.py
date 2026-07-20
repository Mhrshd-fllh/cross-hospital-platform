import logging
import sys
from fastapi import FastAPI, Request, JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from backend.app.api.endpoints import router as api_router
from backend.app.errors import http_exception_handler, unhandled_exception_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)
logger.info("Logging configured.")

app = FastAPI(
    title="Cross-Hospital Generalization Platform Backend",
    version="1.0.0",
    description="Production-grade asynchronous ingestion layer for secure clinical MLOps workflows."
)

# Include the inbound data endpoint router
app.include_router(api_router)

# Register exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
# Handle validation errors (422) to log them
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error for request {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

@app.get("/health", tags=["System Health"])
async def health_check():
    return {"status": "healthy"}