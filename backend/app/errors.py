from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle HTTPException instances.
    Returns a JSON response with the error detail and logs the incident.
    """
    logger.error(f"HTTP {exc.status_code}: {exc.detail} - Path: {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Handle all other exceptions.
    Returns a generic 500 error message and logs the full traceback.
    """
    logger.exception(f"Unhandled exception for request {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please contact support."},
    )