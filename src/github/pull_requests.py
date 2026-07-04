import asyncio

from src.models.schemas import PRInfo, PRReview
from src.utils.exceptions import GitHubClientError
from src.utils.pygithub import GithubException
from src.utils.logger import get_logger
from src.github.client import get_github_client

logger = get_logger(__name__)


def _fetch_prs(owner: str, repo: str, state: str) -> list[PRInfo]:
    client = get_github_client()
    try:
        r = client.get_repo(f"{owner}/{repo}")
        prs = r.get_pulls(state=state, sort="updated", direction="desc")
    except GithubException as e:
        raise GitHubClientError(f"Could not fetch PRs for '{owner}/{repo}'", e.status) from e

    return [
        PRInfo(
            number=pr.number,
            title=pr.title,
            state=pr.state,
            body=pr.body,
            author=pr.user.login if pr.user else "unknown",
            base_branch=pr.base.ref,
            head_branch=pr.head.ref,
            draft=pr.draft,
            mergeable=pr.mergeable,
            review_state=None,
            created_at=pr.created_at,
            updated_at=pr.updated_at,
            url=pr.html_url,
            additions=pr.additions,
            deletions=pr.deletions,
            changed_files=pr.changed_files,
        )
        for pr in prs
    ]


def _fetch_pr(owner: str, repo: str, number: int) -> PRInfo:
    client = get_github_client()
    try:
        r = client.get_repo(f"{owner}/{repo}")
        pr = r.get_pull(number)
    except GithubException as e:
        raise GitHubClientError(f"PR #{number} not found in '{owner}/{repo}'", e.status) from e

    reviews = list(pr.get_reviews())
    review_state = reviews[-1].state if reviews else None

    return PRInfo(
        number=pr.number,
        title=pr.title,
        state=pr.state,
        body=pr.body,
        author=pr.user.login if pr.user else "unknown",
        base_branch=pr.base.ref,
        head_branch=pr.head.ref,
        draft=pr.draft,
        mergeable=pr.mergeable,
        review_state=review_state,
        created_at=pr.created_at,
        updated_at=pr.updated_at,
        url=pr.html_url,
        additions=pr.additions,
        deletions=pr.deletions,
        changed_files=pr.changed_files,
    )


def _fetch_pr_diff(owner: str, repo: str, number: int) -> str:
    """Return a file-by-file summary of the PR diff (not raw patch)."""
    client = get_github_client()
    try:
        r = client.get_repo(f"{owner}/{repo}")
        pr = r.get_pull(number)
        files = list(pr.get_files())
    except GithubException as e:
        raise GitHubClientError(f"Could not fetch diff for PR #{number}", e.status) from e

    lines = [f"PR #{number} — {pr.title}", f"{pr.changed_files} files changed, "
             f"+{pr.additions} -{pr.deletions}", ""]
    for f in files:
        lines.append(f"  [{f.status.upper()}] {f.filename}  +{f.additions} -{f.deletions}")
    return "\n".join(lines)


def _fetch_pr_reviews(owner: str, repo: str, number: int) -> list[PRReview]:
    client = get_github_client()
    try:
        r = client.get_repo(f"{owner}/{repo}")
        pr = r.get_pull(number)
        reviews = pr.get_reviews()
    except GithubException as e:
        raise GitHubClientError(f"Could not fetch reviews for PR #{number}", e.status) from e

    return [
        PRReview(
            reviewer=rv.user.login if rv.user else "unknown",
            state=rv.state,
            submitted_at=rv.submitted_at,
            body=rv.body or None,
        )
        for rv in reviews
    ]




async def list_pull_requests(owner: str, repo: str, state: str = "open") -> list[PRInfo]:
    return await asyncio.to_thread(_fetch_prs, owner, repo, state)

async def get_pull_request(owner: str, repo: str, number: int) -> PRInfo:
    return await asyncio.to_thread(_fetch_pr, owner, repo, number)

async def get_pr_diff(owner: str, repo: str, number: int) -> str:
    return await asyncio.to_thread(_fetch_pr_diff, owner, repo, number)

async def get_pr_reviews(owner: str, repo: str, number: int) -> list[PRReview]:
    return await asyncio.to_thread(_fetch_pr_reviews, owner, repo, number)
