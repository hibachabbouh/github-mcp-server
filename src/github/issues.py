import asyncio

from src.models.schemas import IssueInfo, IssueComment
from src.utils.exceptions import GitHubClientError
from src.utils.pygithub import GithubException
from src.utils.logger import get_logger
from src.github.client import get_github_client

logger = get_logger(__name__)


def _fetch_issues(owner: str, repo: str, state: str, label: str | None, assignee: str | None) -> list[IssueInfo]:
    client = get_github_client()
    try:
        r = client.get_repo(f"{owner}/{repo}")
        kwargs: dict = {"state": state}
        if label:
            kwargs["labels"] = [label]
        if assignee:
            kwargs["assignee"] = assignee
        issues = r.get_issues(**kwargs)
    except GithubException as e:
        raise GitHubClientError(f"Could not fetch issues for '{owner}/{repo}'", e.status) from e

    return [
        IssueInfo(
            number=i.number,
            title=i.title,
            state=i.state,
            body=i.body,
            labels=[l.name for l in i.labels],
            assignees=[a.login for a in i.assignees],
            created_at=i.created_at,
            updated_at=i.updated_at,
            url=i.html_url,
            comments=i.comments,
        )
        for i in issues
        if i.pull_request is None 
    ]


def _fetch_issue(owner: str, repo: str, number: int) -> IssueInfo:
    client = get_github_client()
    try:
        r = client.get_repo(f"{owner}/{repo}")
        i = r.get_issue(number)
    except GithubException as e:
        raise GitHubClientError(f"Issue #{number} not found in '{owner}/{repo}'", e.status) from e

    return IssueInfo(
        number=i.number,
        title=i.title,
        state=i.state,
        body=i.body,
        labels=[l.name for l in i.labels],
        assignees=[a.login for a in i.assignees],
        created_at=i.created_at,
        updated_at=i.updated_at,
        url=i.html_url,
        comments=i.comments,
    )


def _create_issue(owner: str, repo: str, title: str, body: str | None, labels: list[str]) -> IssueInfo:
    client = get_github_client()
    try:
        r = client.get_repo(f"{owner}/{repo}")
        i = r.create_issue(title=title, body=body or "", labels=labels)
    except GithubException as e:
        raise GitHubClientError(f"Could not create issue in '{owner}/{repo}'", e.status) from e

    return IssueInfo(
        number=i.number,
        title=i.title,
        state=i.state,
        body=i.body,
        labels=[l.name for l in i.labels],
        assignees=[],
        created_at=i.created_at,
        updated_at=i.updated_at,
        url=i.html_url,
        comments=0,
    )


def _add_comment(owner: str, repo: str, number: int, body: str) -> IssueComment:
    client = get_github_client()
    try:
        r = client.get_repo(f"{owner}/{repo}")
        i = r.get_issue(number)
        comment = i.create_comment(body)
    except GithubException as e:
        raise GitHubClientError(f"Could not comment on issue #{number}", e.status) from e

    return IssueComment(issue_number=number, comment_id=comment.id, url=comment.html_url)


def _close_issue(owner: str, repo: str, number: int, comment: str | None) -> IssueInfo:
    client = get_github_client()
    try:
        r = client.get_repo(f"{owner}/{repo}")
        i = r.get_issue(number)
        if comment:
            i.create_comment(comment)
        i.edit(state="closed")
        i = r.get_issue(number)  # refresh
    except GithubException as e:
        raise GitHubClientError(f"Could not close issue #{number}", e.status) from e

    return IssueInfo(
        number=i.number,
        title=i.title,
        state=i.state,
        body=i.body,
        labels=[l.name for l in i.labels],
        assignees=[a.login for a in i.assignees],
        created_at=i.created_at,
        updated_at=i.updated_at,
        url=i.html_url,
        comments=i.comments,
    )


# ── Async wrappers ────────────────────────────────────────────────────────────

async def list_issues(owner: str, repo: str, state: str = "open",
                      label: str | None = None, assignee: str | None = None) -> list[IssueInfo]:
    return await asyncio.to_thread(_fetch_issues, owner, repo, state, label, assignee)

async def get_issue(owner: str, repo: str, number: int) -> IssueInfo:
    return await asyncio.to_thread(_fetch_issue, owner, repo, number)

async def create_issue(owner: str, repo: str, title: str,
                       body: str | None = None, labels: list[str] | None = None) -> IssueInfo:
    return await asyncio.to_thread(_create_issue, owner, repo, title, body, labels or [])

async def add_issue_comment(owner: str, repo: str, number: int, body: str) -> IssueComment:
    return await asyncio.to_thread(_add_comment, owner, repo, number, body)

async def close_issue(owner: str, repo: str, number: int, comment: str | None = None) -> IssueInfo:
    return await asyncio.to_thread(_close_issue, owner, repo, number, comment)
