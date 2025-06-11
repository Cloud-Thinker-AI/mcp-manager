from fastapi import APIRouter, Depends, HTTPException
from mcp_manager.server.auth import get_api_key_dependency
from mcp_manager.server.globals import settings
import logging
import json
from typing import List, Dict
import secrets

router = APIRouter()

@router.get("", response_model=List[Dict[str, str]])
async def list_servers(dep=Depends(get_api_key_dependency)):
    try:
        result = await settings.server_manager.list_servers()
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=500, detail=result)
        return result
    except Exception as e:
        logging.error(f"Error in list_servers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{name}/start", response_model=Dict[str, str])
async def start_server(name: str, dep=Depends(get_api_key_dependency)):
    try:
        result = await settings.server_manager.start_server(name)
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=500, detail=result)
        if not result:
            raise HTTPException(status_code=404, detail="Server not found or failed to start")
        return {"status": "started"}
    except Exception as e:
        logging.error(f"Error in start_server: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{name}/stop", response_model=Dict[str, str])
async def stop_server(name: str, dep=Depends(get_api_key_dependency)):
    try:
        result = await settings.server_manager.stop_server(name)
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=500, detail=result)
        if not result:
            raise HTTPException(status_code=404, detail="Server not found or failed to stop")
        return {"status": "stopped"}
    except Exception as e:
        logging.error(f"Error in stop_server: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reload", response_model=Dict[str, str])
async def reload_servers(dep=Depends(get_api_key_dependency)):
    try:
        # Reload the servers config from the config file
        with open(settings.MCP_CONFIG, "r") as f:
            server_config = json.load(f)["mcpServers"]
        # Reload the servers
        settings.server_manager.server_config = server_config
        await settings.server_manager._load_servers_from_config(server_config, reload=True)
        return {"status": "reloaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{name}", response_model=Dict[str, str])
async def remove_server(name: str, dep=Depends(get_api_key_dependency)):
    try:
        await settings.server_manager.remove_server(name)
        return {"status": "removed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/regenerate-api-key", response_model=Dict[str, str])
async def regenerate_api_key(dep=Depends(get_api_key_dependency)):
    new_key = secrets.token_urlsafe(32)
    with open(settings.API_KEY_FILE, "w") as f:
        f.write(new_key)
    settings.API_KEY = new_key
    return {"api_key": new_key}