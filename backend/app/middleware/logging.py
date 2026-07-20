import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from app.utils.logger import get_logger

logger = get_logger("logging_middleware")

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs incoming requests, measures response time,
    and catches unhandled exceptions to return a standardized error response.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        method = request.method
        url = request.url.path
        client_ip = request.client.host if request.client else "unknown"

        logger.info(f"Incoming Request: {method} {url} | Client: {client_ip}")

        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            logger.info(
                f"Request Completed: {method} {url} | Status: {response.status_code} | Duration: {process_time:.2f}ms"
            )
            return response
        except Exception as exc:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"Request Failed: {method} {url} | Duration: {process_time:.2f}ms | Error: {str(exc)}",
                exc_info=True
            )
            # Prevent leaking internal stack traces, return standardized JSON response
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "An unexpected internal server error occurred.",
                    "errors": [str(exc)]
                }
            )
