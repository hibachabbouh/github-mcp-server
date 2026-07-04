from fastmcp import FastMCP
from src.github import repositories
from src.utils.exceptions import GitHubClientError, ToolInputError
from src.utils.logger import get_logger

logger = get_logger(__name__)


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def list_repos(username: str, org: bool = False) -> list[dict]:
        """List repositories for a GitHub user or organization.

        Args:
            username: GitHub username or organization name.
            org: Set to true if username is an organization.
        """
        try:
            repos = await repositories.list_repos(username, org)
            return [r.model_dump(mode="json") for r in repos]
        except GitHubClientError as e:
            raise ValueError(str(e)) from e

    @mcp.tool()
    async def get_repo_info(owner: str, repo: str) -> dict:
        """Get detailed metadata for a repository (stars, forks, language, topics…).

        Args:
            owner: Repository owner (user or org).
            repo: Repository name.
        """
        try:
            info = await repositories.get_repo_info(owner, repo)
            return info.model_dump(mode="json")
        except GitHubClientError as e:
            raise ValueError(str(e)) from e

    @mcp.tool()
    async def get_repo_structure(owner: str, repo: str,
                                  branch: str | None = None, depth: int = 4) -> dict:
        """Browse a repository's directory tree.

        Args:
            owner: Repository owner.
            repo: Repository name.
            branch: Branch to inspect (defaults to the default branch).
            depth: Maximum directory depth to traverse (1–6).
        """
        depth = max(1, min(depth, 6))
        try:
            tree = await repositories.get_repo_tree(owner, repo, branch, depth)
            return tree.model_dump(mode="json")
        except (GitHubClientError, ToolInputError) as e:
            raise ValueError(str(e)) from e

    @mcp.tool()
    async def get_file_content(owner: str, repo: str, path: str,
                                branch: str | None = None) -> dict:
        """Read the content of a file from a repository.

        Args:
            owner: Repository owner.
            repo: Repository name.
            path: File path relative to repo root (e.g. 'src/main.py').
            branch: Branch to read from (defaults to the default branch).
        """
        try:
            content = await repositories.get_file_content(owner, repo, path, branch)
            return content.model_dump(mode="json")
        except (GitHubClientError, ToolInputError) as e:
            raise ValueError(str(e)) from e
