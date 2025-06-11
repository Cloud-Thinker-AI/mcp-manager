from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.responses import JSONResponse
from mcp_manager.server.globals import settings

def get_api_key_dependency(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    if settings.API_KEY is None:
        raise HTTPException(status_code=500, detail="API key not loaded")
    if credentials is None or credentials.scheme.lower() != "bearer" or credentials.credentials != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return True

class MessagesAuthMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            method = scope.get("method", "").upper()
            if path.startswith("/messages") and method == "POST":
                headers = dict((k.decode().lower(), v.decode()) for k, v in scope.get("headers", []))
                auth = headers.get("authorization", "")
                if not auth.startswith("Bearer ") or auth[7:] != settings.API_KEY:
                    response = JSONResponse({"detail": "Invalid or missing API key"}, status_code=401)
                    await response(scope, receive, send)
                    return
        await self.app(scope, receive, send)

class PathPrefixASGIWrapper:
    def __init__(self, app: ASGIApp, prefix: str):
        self.app = app
        self.prefix = prefix

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http" and scope.get("path") is not None:
            scope = dict(scope)
            scope["path"] = self.prefix + scope["path"]
        await self.app(scope, receive, send) 