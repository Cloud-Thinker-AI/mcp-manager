from fastapi import FastAPI
from mcp_manager.core.server_manager import ServerManager
from mcp_manager.server.logging import setup_logging
from mcp_manager.server.auth import MessagesAuthMiddleware, PathPrefixASGIWrapper
from mcp_manager.server.routes import servers, tools, sse, server_sse
from mcp_manager.server.routes.sse import sse_server_transport
from mcp_manager.server.globals import settings
import logging
import os
import json

setup_logging()
app = FastAPI()

# Mount routers
app.include_router(servers.router, prefix="/servers")
app.include_router(tools.router, prefix="/tools")
app.include_router(sse.router)
app.include_router(server_sse.router)

# Mount /messages with middleware
app.mount(
    "/messages",
    MessagesAuthMiddleware(
        PathPrefixASGIWrapper(sse_server_transport.handle_post_message, "/messages"),
    )
)

@app.on_event("startup")
async def startup_event():
    # Template for mcp_config.json
    MCP_CONFIG_TEMPLATE = {
        "mcpServers": {
            "hackernews": {
                "command": "uvx",
                "args": ["mcp-hn"],
                "auto_start": True
            }
        }
    }

    # Check if MCP_CONFIG exists, else create with template
    if not os.path.exists(settings.MCP_CONFIG):
        with open(settings.MCP_CONFIG, "w", encoding="utf-8") as f:
            json.dump(MCP_CONFIG_TEMPLATE, f, indent=2)
    settings.server_manager = await ServerManager().__aenter__()

@app.on_event("shutdown")
async def shutdown_event():
    if settings.server_manager:
        await settings.server_manager.__aexit__(None, None, None)

def main():
    import uvicorn
    import argparse
    parser = argparse.ArgumentParser(description="Start MCP Manager FastAPI server.")
    parser.add_argument("--port", type=int, default=4123, help="Port to run the server on (default: 4123)")
    args = parser.parse_args()
    logging.info(f"Starting MCP Manager FastAPI server on port {args.port}")
    uvicorn.run("mcp_manager.server.main:app", host="0.0.0.0", port=args.port, reload=True)

if __name__ == "__main__":
    main()