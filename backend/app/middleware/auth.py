from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.jwt import decode_token
from app.core.exceptions import ViziCheckException

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware that inspects incoming HTTP requests for Authorization Bearer header.
    Validates JWT claims and attaches user context (request.state.user) if valid.
    """
    async def dispatch(self, request: Request, call_next):
        request.state.user = None
        request.state.tenant_id = None

        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
            try:
                payload = decode_token(token)
                request.state.user = payload
                request.state.tenant_id = payload.get("tenant_id")
            except ViziCheckException:
                # Middleware allows request to pass to route handler where dependencies
                # enforce strict 401/403 errors, or sets state for optional auth routes.
                pass
            except Exception:
                pass

        response = await call_next(request)
        return response
