from fastmcp import FastMCP
from src.github import pull_requests
from src.utils.exceptions import GitHubClientError
from src.utils.logger import get_logger

logger = get_logger(__name__)


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def list_pull_requests(owner: str, repo: str, state: str = "open") -> list[dict]:
        """List pull requests for a repository.

        Args:
            owner: Repository owner.
            repo: Repository name.
            state: 'open', 'closed', or 'all'.
        """
        try:
            result = await pull_requests.list_pull_requests(owner, repo, state)
            return [pr.model_dump(mode="json") for pr in result]
        except GitHubClientError as e:
            raise ValueError(str(e)) from e

    @mcp.tool()
    async def get_pull_request(owner: str, repo: str, number: int) -> dict:
        """Get full details of a pull request including review state.

        Args:
            owner: Repository owner.
            repo: Repository name.
            number: PR number.
        """
        try:
            result = await pull_requests.get_pull_request(owner, repo, number)
            return result.model_dump(mode="json")
        except GitHubClientError as e:
            raise ValueError(str(e)) from e

    @mcp.tool()
    async def get_pr_diff(owner: str, repo: str, number: int) -> str:
        """Get a file-by-file summary of changes in a pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            number: PR number.
        """
        try:
            return await pull_requests.get_pr_diff(owner, repo, number)
        except GitHubClientError as e:
            raise ValueError(str(e)) from e

    @mcp.tool()
    async def get_pr_reviews(owner: str, repo: str, number: int) -> list[dict]:
        """Get all reviews submitted on a pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            number: PR number.
        """
        try:
            result = await pull_requests.get_pr_reviews(owner, repo, number)
            return [r.model_dump(mode="json") for r in result]
        except GitHubClientError as e:
            raise ValueError(str(e)) from e
