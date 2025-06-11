# MCP Manager CLI

A unified CLI and daemon to manage multiple MCP servers with modern UX and robust logging.

**⚡ Powered by [CloudThinker](https://www.cloudthinker.io/)**

## Features

- **Daemon/Service Architecture**: Background FastAPI server for multi-process management
- **Unified CLI**: Interactive CLI for all management operations
- **Server Management**: Start, stop, and monitor multiple MCP servers
- **SSE Support**: Real-time communication endpoints
- **CloudThinker Integration**: Connect with [CloudThinker AI Agents](https://www.cloudthinker.io/)
- **Secure API**: API key authentication for all operations

## Quick Installation

```bash
pip install mcp-manager-cli
```

## Configuration

Create `.cache/mcp_config.json`:
```json
{
  "mcpServers": {
    "hackernews": {
      "command": "uvx",
      "args": ["mcp-hn"],
      "auto_start": true
    }
  }
}
```

## Quick Start

1. **Start the CLI:**
   ```bash
   mcp-manager
   ```

2. **Basic commands:**
   ```bash
   daemon start          # Start daemon (port 4123)
   server list          # List all servers
   tools list           # List available tools
   api-key             # Show API key
   help                # Show all commands
   ```

## Essential Commands

| Command | Description |
|---------|-------------|
| `daemon start [--port PORT]` | Start daemon (default port 4123) |
| `daemon stop` | Stop daemon |
| `daemon status` | Show daemon status |
| `server list` | List managed servers |
| `server reload` | Reload config |
| `tools list` | List all tools |
| `api-key` | Show current API key |
| `config edit` | Edit configuration |

## API Endpoints

- **Management**: All endpoints require API key authentication
- **SSE Stream**: `GET /sse` - Unified stream for all servers
- **Per-Server SSE**: `GET /<server-name>/sse` - Direct server access
- **Messages**: `POST /messages` - Send messages to servers

## Docker Usage

```bash
# Quick start with Docker Compose
docker-compose up -d

# Or run directly
docker run -d -p 4123:4123 \
  -v $(pwd)/.cache:/app/.cache \
  khaitrinhxuan/mcp-manager-cli:latest
```

## Security

- API key auto-generated in `.cache/mcp_manager_api_key.txt`
- All management endpoints require Bearer token authentication
- Use `regenerate-api-key` command to create new key

## Integration Examples

### With ngrok
```bash
ngrok http 4123
```

### With Cursor
Use [supergateway](https://github.com/supercorp-ai/supergateway):
```json
{
  "mcpServers": {
    "mcp-manager": {
      "command": "npx",
      "args": ["-y", "supergateway", "--sse", "http://localhost:4123/sse", "--oauth2Bearer", "YOUR-API-KEY"]
    }
  }
}
```

## CloudThinker Integration

For comprehensive setup guide: **[Official CloudThinker Documentation](https://docs.cloudthinker.io/how-to-guide/agent-orchestration/connectors/deploy-multiples-and-secure-mcp-from-your-private-environment-with-mcp-manager)**

Learn more at [cloudthinker.io](https://www.cloudthinker.io/)

## Development Setup

```bash
# Clone and setup
git clone <repo-url>
cd mcp-manager
uv venv .venv
source .venv/bin/activate
uv pip install -e .
```

## File Structure

- **Config**: `.cache/mcp_config.json`
- **API Key**: `.cache/mcp_manager_api_key.txt`  
- **Logs**: `.cache/mcp_manager_daemon.log`

## License

[MIT License](LICENSE)