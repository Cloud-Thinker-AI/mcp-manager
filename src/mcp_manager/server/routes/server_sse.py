from fastapi import APIRouter, Depends, Request, HTTPException, Response
from mcp_manager.server.auth import get_api_key_dependency, MessagesAuthMiddleware, PathPrefixASGIWrapper
from mcp.server.lowlevel import Server
from mcp_manager.server.globals import settings
from mcp.types import TextContent, ImageContent, EmbeddedResource, Tool

router = APIRouter()

@router.api_route("/{mcp_server_name}/sse", methods=["GET"])
async def sse_endpoint(
    mcp_server_name: str,
    request: Request,
    dep=Depends(get_api_key_dependency)
):
    if not await settings.server_manager.check_server_exists_and_running(mcp_server_name):
        raise HTTPException(status_code=404, detail="Server not found")
    
    sse_server_transport = settings.SSE_SERVER_TRANSPORT.get(mcp_server_name)
    if not sse_server_transport:
        raise HTTPException(status_code=404, detail="Server not found")
    
    mcp_server = Server(mcp_server_name)

    @mcp_server.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[TextContent | ImageContent | EmbeddedResource]:
        """
        Call handler for all registered tools.
        """
        return await settings.server_manager.call_server_tool(mcp_server_name, name, arguments)

    @mcp_server.list_tools()
    async def list_tools() -> list[Tool]:
        """
        List all available tools.
        """
        return await settings.server_manager.list_server_tools(mcp_server_name)
    
    async with sse_server_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp_server.run(
            streams[0], streams[1], mcp_server.create_initialization_options()
        )

@router.api_route("/{mcp_server_name}/messages", methods=["POST"])
async def post_message_endpoint(
    mcp_server_name: str,
    request: Request,
    dep=Depends(get_api_key_dependency)
):
    if not await settings.server_manager.check_server_exists_and_running(mcp_server_name):
        raise HTTPException(status_code=404, detail="Server not found")
    
    sse_server_transport = settings.SSE_SERVER_TRANSPORT.get(mcp_server_name)
    if not sse_server_transport:
        raise HTTPException(status_code=404, detail="Server not found")
    
    asgi_app = MessagesAuthMiddleware(
        PathPrefixASGIWrapper(sse_server_transport.handle_post_message, f"/{mcp_server_name}/messages")
    )

    # Prepare to collect the ASGI response
    response_start = {}
    body_chunks = []

    async def send(message):
        if message["type"] == "http.response.start":
            response_start["status"] = message["status"]
            response_start["headers"] = {k.decode(): v.decode() for k, v in message.get("headers", [])}
        elif message["type"] == "http.response.body":
            chunk = message.get("body", b"")
            if chunk:
                body_chunks.append(chunk)

    await asgi_app(request.scope, request.receive, send)

    status = response_start.get("status", 200)
    headers = response_start.get("headers", {})
    body = b"".join(body_chunks)
    return Response(content=body, status_code=status, headers=headers)
