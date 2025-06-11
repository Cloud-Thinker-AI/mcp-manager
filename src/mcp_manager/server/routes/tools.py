from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List
from mcp_manager.server.auth import get_api_key_dependency
from mcp_manager.server.globals import settings
import logging
from mcp.types import Tool

router = APIRouter()

@router.get("", response_model=List[Tool])
async def list_tools(dep=Depends(get_api_key_dependency)):
    try:
        result = await settings.server_manager.list_tools()
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=500, detail=result)
        return result
    except Exception as e:
        logging.error(f"Error in list_tools: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    