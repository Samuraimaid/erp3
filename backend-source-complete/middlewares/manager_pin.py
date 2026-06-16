from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from backend.core.security import get_user_by_token, verify_manager_pin

class ManagerPinMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/approvals/resolve") and request.method in ("PATCH",):
            data = await request.json()
            pin = data.get("pin")
            token = request.headers.get("Authorization")
            user = get_user_by_token(token)
            if not user or user.role != "gerencia":
                raise HTTPException(403, "Solo gerencia puede resolver")
            if not verify_manager_pin(user.id, pin):
                raise HTTPException(403, "PIN de gerente incorrecto")
        response = await call_next(request)
        return response
