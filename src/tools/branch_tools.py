from fastmcp import FastMCP
from src.github import branches
from src.utils.exceptions import GitHubClientError
from src.utils.logger import get_logger

logger = get_logger(__name__)


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def list_branches(owner: str, repo: str) -> list[dict]:
        """List all branches of a repository with protection status and staleness flag.

        Args:
            owner: Repository owner.
            repo: Repository name.
        """
        try:
            result = await branches.list_branches(owner, repo)
            return [b.model_dump(mode="json") for b in result]
        except GitHubClientError as e:
            raise ValueError(str(e)) from e

    @mcp.tool()
    async def get_branch_info(owner: str, repo: str, branch: str) -> dict:
        """Get details for a specific branch (last commit, author, staleness).

        Args:
            owner: Repository owner.
            repo: Repository name.
            branch: Branch name.
        """
        try:
            result = await branches.get_branch_info(owner, repo, branch)
            return result.model_dump(mode="json")
        except GitHubClientError as e:
            raise ValueError(str(e)) from e

    @mcp.tool()
    async def compare_branches(owner: str, repo: str, base: str, head: str) -> dict:
        """Compare two branches: ahead/behind counts, files changed, additions/deletions.

        Args:
            owner: Repository owner.
            repo: Repository name.
            base: Base branch name.
            head: Head branch name.
        """
        try:
            result = await branches.compare_branches(owner, repo, base, head)
            return result.model_dump(mode="json")
        except GitHubClientError as e:
            raise ValueError(str(e)) from e

    @mcp.tool()
    async def detect_stale_branches(owner: str, repo: str) -> list[dict]:
        """List branches that have had no commits for more than STALE_BRANCH_DAYS days.

        Args:
            owner: Repository owner.
            repo: Repository name.
        """
        try:
            result = await branches.detect_stale_branches(owner, repo)
            return [b.model_dump(mode="json") for b in result]
        except GitHubClientError as e:
            raise ValueError(str(e)) from e
