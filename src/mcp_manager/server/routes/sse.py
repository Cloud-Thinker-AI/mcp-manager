from fastapi import APIRouter, Depends, Request
from mcp_manager.server.auth import get_api_key_dependency
from mcp.server.sse import SseServerTransport
from mcp.server.lowlevel import Server
from mcp.types import TextContent, ImageContent, EmbeddedResource, Tool
from mcp_manager.server.globals import settings

router = APIRouter()

sse_server_transport = SseServerTransport("/messages/")
mcp_server = Server("mcp-manager")

async def handle_sse(request: Request):
    async with sse_server_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp_server.run(
            streams[0], streams[1], mcp_server.create_initialization_options()
        )

@mcp_server.call_tool()
async def call_tool(
    name: str, arguments: dict
) -> list[TextContent | ImageContent | EmbeddedResource]:
    """
    Call handler for all registered tools.
    """
    return await settings.server_manager.call_tool(name, arguments)

@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """
    List all available tools.
    """
    return await settings.server_manager.list_tools()

@router.api_route("/sse", methods=["GET"])
async def sse_endpoint(request: Request, dep=Depends(get_api_key_dependency)):
    return await handle_sse(request) 