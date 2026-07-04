import asyncio
from datetime import datetime, timezone, timedelta

from src.models.schemas import BranchInfo, BranchComparison
from src.utils.exceptions import GitHubClientError
from src.utils.pygithub import GithubException
from src.utils.logger import get_logger
from src.config import settings
from src.github.client import get_github_client

logger = get_logger(__name__)


def _fetch_branches(owner: str, repo: str) -> list[BranchInfo]:
    client = get_github_client()
    try:
        r = client.get_repo(f"{owner}/{repo}")
        branches = r.get_branches()
    except GithubException as e:
        raise GitHubClientError(f"Could not fetch branches for '{owner}/{repo}'", e.status) from e

    stale_cutoff = datetime.now(timezone.utc) - timedelta(days=settings.stale_branch_days)
    result = []
    for b in branches:
        commit = b.commit
        commit_date = commit.commit.author.date if commit.commit.author else None
        if commit_date and commit_date.tzinfo is None:
            commit_date = commit_date.replace(tzinfo=timezone.utc)

        result.append(BranchInfo(
            name=b.name,
            sha=commit.sha,
            protected=b.protected,
            last_commit_date=commit_date,
            last_commit_message=commit.commit.message.splitlines()[0] if commit.commit.message else None,
            last_commit_author=commit.commit.author.name if commit.commit.author else None,
            is_stale=bool(commit_date and commit_date < stale_cutoff),
        ))
    return result


def _fetch_branch_info(owner: str, repo: str, branch: str) -> BranchInfo:
    client = get_github_client()
    try:
        r = client.get_repo(f"{owner}/{repo}")
        b = r.get_branch(branch)
    except GithubException as e:
        raise GitHubClientError(f"Branch '{branch}' not found in '{owner}/{repo}'", e.status) from e

    stale_cutoff = datetime.now(timezone.utc) - timedelta(days=settings.stale_branch_days)
    commit = b.commit
    commit_date = commit.commit.author.date if commit.commit.author else None
    if commit_date and commit_date.tzinfo is None:
        commit_date = commit_date.replace(tzinfo=timezone.utc)

    return BranchInfo(
        name=b.name,
        sha=commit.sha,
        protected=b.protected,
        last_commit_date=commit_date,
        last_commit_message=commit.commit.message.splitlines()[0] if commit.commit.message else None,
        last_commit_author=commit.commit.author.name if commit.commit.author else None,
        is_stale=bool(commit_date and commit_date < stale_cutoff),
    )


def _compare_branches(owner: str, repo: str, base: str, head: str) -> BranchComparison:
    client = get_github_client()
    try:
        r = client.get_repo(f"{owner}/{repo}")
        comparison = r.compare(base, head)
    except GithubException as e:
        raise GitHubClientError(f"Could not compare '{base}' and '{head}'", e.status) from e

    return BranchComparison(
        base=base,
        head=head,
        ahead_by=comparison.ahead_by,
        behind_by=comparison.behind_by,
        files_changed=comparison.total_commits,
        additions=sum(f.additions for f in comparison.files),
        deletions=sum(f.deletions for f in comparison.files),
    )



async def list_branches(owner: str, repo: str) -> list[BranchInfo]:
    return await asyncio.to_thread(_fetch_branches, owner, repo)

async def get_branch_info(owner: str, repo: str, branch: str) -> BranchInfo:
    return await asyncio.to_thread(_fetch_branch_info, owner, repo, branch)

async def compare_branches(owner: str, repo: str, base: str, head: str) -> BranchComparison:
    return await asyncio.to_thread(_compare_branches, owner, repo, base, head)

async def detect_stale_branches(owner: str, repo: str) -> list[BranchInfo]:
    branches = await list_branches(owner, repo)
    return [b for b in branches if b.is_stale]
