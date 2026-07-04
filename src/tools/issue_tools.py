from fastmcp import FastMCP
from src.github import issues
from src.utils.exceptions import GitHubClientError
from src.utils.logger import get_logger

logger = get_logger(__name__)


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def list_issues(owner: str, repo: str, state: str = "open",
                          label: str | None = None, assignee: str | None = None) -> list[dict]:
        """List issues for a repository.

        Args:
            owner: Repository owner.
            repo: Repository name.
            state: 'open', 'closed', or 'all'.
            label: Filter by label name.
            assignee: Filter by assignee login.
        """
        try:
            result = await issues.list_issues(owner, repo, state, label, assignee)
            return [i.model_dump(mode="json") for i in result]
        except GitHubClientError as e:
            raise ValueError(str(e)) from e

    @mcp.tool()
    async def get_issue(owner: str, repo: str, number: int) -> dict:
        """Get full details of a specific issue including body and comment count.

        Args:
            owner: Repository owner.
            repo: Repository name.
            number: Issue number.
        """
        try:
            result = await issues.get_issue(owner, repo, number)
            return result.model_dump(mode="json")
        except GitHubClientError as e:
            raise ValueError(str(e)) from e

    @mcp.tool()
    async def create_issue(owner: str, repo: str, title: str,
                           body: str | None = None, labels: list[str] | None = None) -> dict:
        """Create a new issue in a repository.

        Args:
            owner: Repository owner.
            repo: Repository name.
            title: Issue title.
            body: Issue description (Markdown supported).
            labels: List of label names to apply.
        """
        try:
            result = await issues.create_issue(owner, repo, title, body, labels)
            return result.model_dump(mode="json")
        except GitHubClientError as e:
            raise ValueError(str(e)) from e

    @mcp.tool()
    async def add_issue_comment(owner: str, repo: str, number: int, body: str) -> dict:
        """Add a comment to an existing issue.

        Args:
            owner: Repository owner.
            repo: Repository name.
            number: Issue number.
            body: Comment body (Markdown supported).
        """
        try:
            result = await issues.add_issue_comment(owner, repo, number, body)
            return result.model_dump(mode="json")
        except GitHubClientError as e:
            raise ValueError(str(e)) from e

    @mcp.tool()
    async def close_issue(owner: str, repo: str, number: int,
                          comment: str | None = None) -> dict:
        """Close an issue, optionally leaving a resolution comment.

        Args:
            owner: Repository owner.
            repo: Repository name.
            number: Issue number.
            comment: Optional closing comment.
        """
        try:
            result = await issues.close_issue(owner, repo, number, comment)
            return result.model_dump(mode="json")
        except GitHubClientError as e:
            raise ValueError(str(e)) from e
