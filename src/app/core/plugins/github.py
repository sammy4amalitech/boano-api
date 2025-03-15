from typing import Dict, Any
import httpx
from ..plugins import PluginBase, PluginRegistry

class GitHubPlugin(PluginBase):
    """GitHub integration plugin."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    @property
    def name(self) -> str:
        return "github"

    @property
    def description(self) -> str:
        return "GitHub integration for repository access and management"

    @property
    def auth_type(self) -> str:
        return "oauth2"

    @property
    def required_scopes(self) -> list[str]:
        return ["repo", "read:user"]

    async def authenticate(self, code: str = None, **kwargs) -> Dict[str, Any]:
        """Handle GitHub OAuth authentication."""
        if not code:
            # Return the authorization URL if no code is provided
            scopes = " ".join(self.required_scopes)
            auth_url = (
                f"https://github.com/login/oauth/authorize"
                f"?client_id={self.client_id}"
                f"&redirect_uri={self.redirect_uri}"
                f"&scope={scopes}"
            )
            return {"redirect_url": auth_url}

        # Exchange code for access token
        token_url = "https://github.com/login/oauth/access_token"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                headers={"Accept": "application/json"},
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                },
            )
            token_data = response.json()

        if "access_token" not in token_data:
            raise ValueError("GitHub authentication failed")

        return token_data

    async def validate_auth(self, auth_data: Dict[str, Any]) -> bool:
        """Validate GitHub authentication data."""
        if "access_token" not in auth_data:
            return False

        # Test the token by making a request to GitHub API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {auth_data['access_token']}",
                    "Accept": "application/json",
                },
            )
            return response.status_code == 200

# Register the GitHub plugin
def register_github_plugin(client_id: str, client_secret: str, redirect_uri: str) -> None:
    """Register GitHub plugin with the plugin registry."""
    plugin = GitHubPlugin(client_id, client_secret, redirect_uri)
    PluginRegistry.register(plugin)