import json
import asyncio
from typing import Dict, List, Union
from mcp import StdioServerParameters
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp_manager.core.server import StdioServer, SSEServer
import logging
from mcp.server.sse import SseServerTransport

class ServerManager:
    def __init__(self):
        self.servers: Dict[str, Union[StdioServer, SSEServer]] = {}
        self.server_tasks: Dict[str, asyncio.Task] = {}  # Track server run tasks

        # Load servers from global config
        from mcp_manager.server.globals import settings
        with open(settings.MCP_CONFIG, "r") as f:
            self.server_config = json.load(f)["mcpServers"]

    async def __aenter__(self):
        await self._load_servers_from_config(self.server_config)
        return self
    
    async def __aexit__(self, *excinfo):
        for server in self.servers.values():
            await server.__aexit__(*excinfo)

    async def _load_servers_from_config(self, server_config: Dict[str, dict], reload: bool = False) -> None:
        """
        Load servers from the server config.
        """
        from mcp_manager.server.globals import settings

        # Remove servers that are not in the new config
        if reload:
            for name in list(self.servers.keys()):
                if name not in server_config:
                    await self.remove_server(name)
                    settings.SSE_SERVER_TRANSPORT.pop(name, None)

        for name, entry in server_config.items():
            if reload and name in self.servers:
                if isinstance(self.servers[name], SSEServer):
                    # SSE server
                    # TODO: Implement SSE server reload
                    pass
                else:
                    # Stdio server
                    # Check if command, args, or env changed
                    old_server = self.servers[name]
                    old_params = getattr(old_server, 'params', None)
                    old_command = getattr(old_params, 'command', None) if old_params else None
                    old_args = getattr(old_params, 'args', None) if old_params else None
                    old_env = getattr(old_params, 'env', None) if old_params else None
                    new_command = entry.get("command")
                    new_args = entry.get("args", [])
                    new_env = entry.get("env", {})
                    if (
                        old_command == new_command and
                        old_args == new_args and
                        old_env == new_env
                    ):
                        logging.info(f"No change in {name}, skipping reload")
                        continue  # No change, skip
                    logging.info(f"Reloading {name}")
                    # If changed, remove and reload this server
                    await self.remove_server(name)
                    settings.SSE_SERVER_TRANSPORT.pop(name, None)

            if entry.get("command") is None:
                # TODO: Implement SSE server
                pass
            else:
                params = StdioServerParameters(
                    command=entry.get("command"),
                    args=entry.get("args", []),
                    env=entry.get("env", {})
                )
                server = StdioServer(params=params, name=name, auto_start=entry.get("auto_start", False))
                self.servers[name] = server
                if entry.get("auto_start", False):
                    # Start the server's run loop as a background task
                    self.server_tasks[name] = asyncio.create_task(server.run())
                    settings.SSE_SERVER_TRANSPORT[name] = SseServerTransport(f"/{name}/messages")

    async def list_servers(self) -> List[Dict[str, str]]:
        try:
            return [
                {
                    "name": server_name,
                    "status": server.get_status().value,
                }
                for server_name, server in self.servers.items()
            ]
        except Exception as e:
            logging.error(f"Error in list_servers: {e}")
            return []

    async def start_server(self, name: str) -> bool:
        try:
            if name not in self.servers:
                return False
            # If already running, do nothing
            if self.servers[name].get_status() == "running":
                return True
            # Start the server's run loop as a background task
            self.server_tasks[name] = asyncio.create_task(self.servers[name].run())
            # Add the SSE server transport
            from mcp_manager.server.globals import settings
            settings.SSE_SERVER_TRANSPORT[name] = SseServerTransport(f"/{name}/messages")
            return True
        except Exception as e:
            logging.error(f"Error in start_server({name}): {e}")
            return False

    async def stop_server(self, name: str) -> bool:
        try:
            if name not in self.servers:
                return False
            await self.servers[name].request_disconnect()
            # Optionally, await the task to ensure shutdown
            if name in self.server_tasks:
                await self.server_tasks[name]
                del self.server_tasks[name]
            # Remove the SSE server transport
            from mcp_manager.server.globals import settings
            settings.SSE_SERVER_TRANSPORT.pop(name, None)
            return True
        except Exception as e:
            logging.error(f"Error in stop_server({name}): {e}")
            return False
    
    async def remove_server(self, name: str) -> bool:
        try:
            if name not in self.servers:
                return False
            await self.stop_server(name)
            del self.servers[name]
            return True 
        except Exception as e:
            logging.error(f"Error in remove_server({name}): {e}")
            return False

    async def get_server_status(self, name: str) -> dict:
        try:
            if not name in self.servers:
                return {"name": name, "status": "not_found"}
            return {
                "name": name,
                "status": self.servers[name].status.value,
            }
        except Exception as e:
            logging.error(f"Error in get_server_status({name}): {e}")
            return {}
    
    async def list_tools(self) -> List[Tool]:
        try:
            tools = []
            for server_name in self.servers.keys():
                server_tools = await self.list_server_tools(server_name)
                for tool in server_tools:
                    tool.name = f"{server_name}__{tool.name}"
                    tools.append(tool)
            return tools
        except Exception as e:
            return []

    async def list_server_tools(self, server_name: str) -> List[Tool]:
        try:
            if not server_name in self.servers:
                return []
            tools = await self.servers[server_name].list_tools()
            return tools
        except Exception as e:
            logging.error(f"Error in list_server_tools({server_name}): {e}")
            return []

    async def call_tool(self, tool_name: str, arguments: dict) -> List[TextContent | ImageContent | EmbeddedResource]:
        try:
            if "__" not in tool_name:
                raise ValueError("Tool name must be in format server__tool")
            server_name, real_tool_name = tool_name.split("__", 1)
            return await self.call_server_tool(server_name, real_tool_name, arguments)
        except Exception as e:
            logging.error(f"Error in call_tool({tool_name}): {e}")
            return []

    async def call_server_tool(self, server_name: str, tool_name: str, arguments: dict) -> List[TextContent | ImageContent | EmbeddedResource]:
        try:
            if not server_name in self.servers:
                return []
            tool_result =  await self.servers[server_name].call_tool(tool_name, arguments)
            return tool_result
        except Exception as e:
            logging.error(f"Error in call_server_tool({server_name}, {tool_name}): {e}")
            return []
    
    async def check_server_exists_and_running(self, server_name: str) -> bool:
        """ 
        Check if the server exists in the server manager.
        Check if the server is running.
        """
        if not server_name in self.servers:
            return False
        return self.servers[server_name].get_status() == "running"