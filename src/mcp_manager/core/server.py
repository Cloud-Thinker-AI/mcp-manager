from typing import Any, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.client.stdio import stdio_client
from mcp_manager.models.server import ServerStatus
import asyncio

class StdioServer:
    """
    Represents an MCP server connected via stdio (local process).
    Supports cross-task disconnect requests via an asyncio.Event.
    """
    def __init__(self, params: StdioServerParameters, name: str = None, auto_start: bool = False):
        self.params = params
        self.name = name
        self.client_ctx = None
        self.session: Optional[ClientSession] = None
        self.status = ServerStatus.STOPPED
        self.auto_start = auto_start
        self._disconnect_event = asyncio.Event()
        self._main_task = None
    
    async def __aenter__(self):
        if self.auto_start:
            await self.connect()
        return self
    
    async def __aexit__(self, *excinfo):
        await self.request_disconnect()
        # Wait for disconnect to complete
        if self._main_task:
            await self._main_task

    def get_status(self) -> ServerStatus:
        return self.status

    async def connect(self):
        """Connect to the server."""
        if self.status == ServerStatus.RUNNING:
            return
        # Connect to the server
        self.status = ServerStatus.STARTING
        self.client_ctx = stdio_client(self.params)
        read, write = await self.client_ctx.__aenter__()
        self.session = await ClientSession(read, write).__aenter__()
        self.status = ServerStatus.RUNNING
        await self.session.initialize()

    async def run(self):
        """Main server task: connect, then wait for disconnect event, then disconnect."""
        await self.connect()
        self._main_task = asyncio.current_task()
        try:
            await self._disconnect_event.wait()
        finally:
            await self.disconnect()

    async def request_disconnect(self):
        """Request disconnect from any task/context."""
        self._disconnect_event.set()

    async def disconnect(self):
        """Disconnect from the server (must be called from main task)."""
        if self.status == ServerStatus.STOPPED:
            return
        # Disconnect from the server
        if self.session:
            await self.session.__aexit__(None, None, None)
            self.session = None
        if self.client_ctx:
            await self.client_ctx.__aexit__(None, None, None)
            self.client_ctx = None
        self.status = ServerStatus.STOPPED
        self._disconnect_event.clear()
        
    async def list_tools(self) -> List[Tool]:
        if self.status == ServerStatus.STOPPED or not self.session:
            raise RuntimeError("Not connected.")
        tools = await self.session.list_tools()
        return tools.tools

    async def call_tool(self, tool_name: str, arguments: Dict) -> List[TextContent | ImageContent | EmbeddedResource]:
        if self.status == ServerStatus.STOPPED or not self.session:
            raise RuntimeError("Not connected.")
        tool_result = await self.session.call_tool(tool_name, arguments)
        return tool_result.content

class SSEServer:
    pass