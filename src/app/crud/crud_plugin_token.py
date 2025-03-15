from fastcrud import FastCRUD

from ..models.plugin_token import (
    PluginToken,
    PluginTokenCreateInternal,
    PluginTokenDelete,
    PluginTokenRead,
    PluginTokenUpdate,
    PluginTokenUpdateInternal,
)

CRUDPluginToken = FastCRUD[PluginToken, PluginTokenCreateInternal, PluginTokenUpdate, PluginTokenUpdateInternal,
                                                    PluginTokenDelete, PluginTokenRead]
crud_plugin_tokens = CRUDPluginToken(PluginToken)
