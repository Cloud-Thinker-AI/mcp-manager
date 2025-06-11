from mcp_manager.core.server_manager import ServerManager
from mcp_manager.utils.loader import load_api_key
import os
from mcp.server.sse import SseServerTransport

CACHE_DIR = ".cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

class Settings:
    server_manager: ServerManager = None
    API_KEY_FILE: str = os.path.join(CACHE_DIR, "mcp_manager_api_key.txt")
    API_KEY: str = load_api_key(API_KEY_FILE)
    LOG_FILE: str = os.path.join(CACHE_DIR, 'mcp_manager_daemon.log')
    MCP_CONFIG: str = os.path.join(CACHE_DIR, "mcp_config.json")
    SSE_SERVER_TRANSPORT: dict[str, SseServerTransport] = {}

settings = Settings()