# Import your plugins
from .core.plugins.github import register_github_plugin
from .api import router
from .core.config import settings
from .core.setup import create_application

# Register GitHub plugin with credentials from settings
register_github_plugin(
    client_id=settings.GITHUB_CLIENT_ID,
    client_secret=settings.GITHUB_CLIENT_SECRET,
    redirect_uri=settings.GITHUB_REDIRECT_URI
)

app = create_application(router=router, settings=settings)
