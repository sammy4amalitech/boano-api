from typing import Annotated, Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from ...core.db.database import async_get_db
from ...core.plugins import PluginRegistry
from ...crud.crud_plugin_token import crud_plugin_tokens
from ...models.plugin_token import PluginTokenCreateInternal
from ...models.user import UserRead
from ..dependencies import get_current_user

router = APIRouter(prefix="/plugins", tags=["plugins"])

class CodeExchangeRequest(BaseModel):
    code: str

@router.get("/")
async def list_plugins(current_user = Depends(get_current_user)):
    """List all available plugins in the marketplace."""
    plugins = PluginRegistry.list_plugins()
    return {
        "plugins": [
            {
                "name": plugin.name,
                "description": plugin.description,
                "auth_type": plugin.auth_type,
                "required_scopes": plugin.required_scopes
            }
            for plugin in plugins.values()
        ]
    }

@router.get("/{plugin_name}/auth")
async def initiate_auth(plugin_name: str):
    """Initiate authentication flow for a specific plugin."""
    plugin = PluginRegistry.get_plugin(plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin {plugin_name} not found")
    auth_data = await plugin.authenticate()
    return auth_data

@router.post("/{plugin_name}/token")
async def exchange_code_for_token(plugin_name: str, request: CodeExchangeRequest,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    """Exchange OAuth code for access token and store it for the user.

    This endpoint is called by the frontend after receiving the authorization code
    from the OAuth provider's redirect.
    """
    plugin = PluginRegistry.get_plugin(plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin {plugin_name} not found")

    try:
        # Exchange the code for an access token using the plugin
        token_data = await plugin.authenticate(code=request.code)
        # Validate the token
        is_valid = await plugin.validate_auth(token_data)
        if not is_valid:
            raise HTTPException(status_code=401, detail=f"Invalid {plugin_name} token")
        # Store the token for the user using crud_plugin_tokens
        try:
            token_create = PluginTokenCreateInternal(
                plugin_name=plugin_name,
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                expires_at=token_data.get("expires_at"),
                raw_token_data=token_data,
                user_id=current_user["id"]
            )
            await crud_plugin_tokens.create(db, token_create )
            return token_data
        except Exception as e:
            print('Token creation error:', e)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{plugin_name}/validate")
async def validate_auth(plugin_name: str, auth_data: Dict[str, Any]):
    """Validate authentication data for a plugin."""
    plugin = PluginRegistry.get_plugin(plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin {plugin_name} not found")

    is_valid = await plugin.validate_auth(auth_data)
    return {"is_valid": is_valid}
