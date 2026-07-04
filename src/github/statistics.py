import asyncio

from src.models.schemas import RepoStats, ContributorStats
from src.utils.exceptions import GitHubClientError
from src.utils.pygithub import GithubException
from src.utils.logger import get_logger
from src.github.client import get_github_client

logger = get_logger(__name__)


def _fetch_stats(owner: str, repo: str) -> RepoStats:
    client = get_github_client()
    try:
        r = client.get_repo(f"{owner}/{repo}")
        contributor_stats = r.get_stats_contributors() or []
        open_prs = r.get_pulls(state="open").totalCount
    except GithubException as e:
        raise GitHubClientError(f"Could not fetch stats for '{owner}/{repo}'", e.status) from e

    contributors = []
    total_commits = 0

    for cs in contributor_stats:
        if cs.author is None:
            continue
        weeks = cs.weeks
        commits = sum(w.c for w in weeks)
        additions = sum(w.a for w in weeks)
        deletions = sum(w.d for w in weeks)
        total_commits += commits
        contributors.append(ContributorStats(
            login=cs.author.login,
            commits=commits,
            additions=additions,
            deletions=deletions,
        ))

    contributors.sort(key=lambda c: c.commits, reverse=True)

    return RepoStats(
        full_name=r.full_name,
        total_commits_last_year=total_commits,
        contributors=contributors[:20],
        open_issues=r.open_issues_count,
        open_prs=open_prs,
    )


async def get_repo_stats(owner: str, repo: str) -> RepoStats:
    return await asyncio.to_thread(_fetch_stats, owner, repo)
