from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class PluginBase(ABC):
    """Base class for all marketplace plugins."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the plugin."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """A description of what the plugin does."""
        pass
    
    @property
    @abstractmethod
    def auth_type(self) -> str:
        """The authentication type (e.g., 'oauth2', 'api_key')."""
        pass
    
    @property
    @abstractmethod
    def required_scopes(self) -> list[str]:
        """List of required scopes for the plugin."""
        pass
    
    @abstractmethod
    async def authenticate(self, **kwargs) -> Dict[str, Any]:
        """Handle plugin authentication."""
        pass
    
    @abstractmethod
    async def validate_auth(self, auth_data: Dict[str, Any]) -> bool:
        """Validate authentication data."""
        pass

class PluginRegistry:
    """Registry for managing marketplace plugins."""
    
    _plugins: Dict[str, PluginBase] = {}
    
    @classmethod
    def register(cls, plugin: PluginBase) -> None:
        """Register a new plugin."""
        cls._plugins[plugin.name] = plugin
    
    @classmethod
    def get_plugin(cls, name: str) -> Optional[PluginBase]:
        """Get a plugin by name."""
        return cls._plugins.get(name)
    
    @classmethod
    def list_plugins(cls) -> Dict[str, PluginBase]:
        """List all registered plugins."""
        return cls._plugins.copy()