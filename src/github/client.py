from src.config import settings
from src.utils.pygithub import Auth, Github
from src.utils.logger import get_logger

logger = get_logger(__name__)

_client: Github | None = None


def get_github_client() -> Github:
    """Return the singleton authenticated GitHub client."""
    global _client
    if _client is None:
        auth = Auth.Token(settings.github_token)
        _client = Github(auth=auth, per_page=100)
        logger.info("GitHub client initialized")
    return _client
