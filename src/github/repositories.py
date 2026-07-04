import asyncio
import base64

from src.models.schemas import RepoInfo, RepoTree, FileNode, FileContent
from src.utils.exceptions import GitHubClientError, ToolInputError
from src.utils.pygithub import GithubException, Repository as GHRepo
from src.utils.logger import get_logger
from src.config import settings
from src.github.client import get_github_client

logger = get_logger(__name__)


def _get_repo(owner: str, repo: str) -> GHRepo:
    try:
        return get_github_client().get_repo(f"{owner}/{repo}")
    except GithubException as e:
        raise GitHubClientError(f"Repository '{owner}/{repo}' not found or inaccessible", e.status) from e


def _fetch_repo_info(owner: str, repo: str) -> RepoInfo:
    r = _get_repo(owner, repo)
    return RepoInfo(
        full_name=r.full_name,
        description=r.description,
        language=r.language,
        stars=r.stargazers_count,
        forks=r.forks_count,
        open_issues=r.open_issues_count,
        default_branch=r.default_branch,
        topics=r.get_topics(),
        visibility="private" if r.private else "public",
        created_at=r.created_at,
        updated_at=r.updated_at,
        url=r.html_url,
    )


def _fetch_repo_tree(owner: str, repo: str, branch: str | None, depth: int) -> RepoTree:
    r = _get_repo(owner, repo)
    ref = branch or r.default_branch
    try:
        tree = r.get_git_tree(ref, recursive=True).tree
    except GithubException as e:
        raise GitHubClientError(f"Could not fetch tree for branch '{ref}'", e.status) from e

    nodes: list[FileNode] = []
    for item in tree:
        item_depth = item.path.count("/")
        if item_depth >= depth:
            continue
        nodes.append(FileNode(path=item.path, type=item.type, size=item.size))

    return RepoTree(full_name=r.full_name, branch=ref, nodes=nodes)


def _fetch_file_content(owner: str, repo: str, path: str, branch: str | None) -> FileContent:
    r = _get_repo(owner, repo)
    ref = branch or r.default_branch
    try:
        file = r.get_contents(path, ref=ref)
    except GithubException as e:
        raise GitHubClientError(f"File '{path}' not found on branch '{ref}'", e.status) from e

    if isinstance(file, list):
        raise ToolInputError(f"'{path}' is a directory, not a file")

    size_kb = (file.size or 0) / 1024
    if size_kb > settings.max_file_size_kb:
        raise ToolInputError(f"File too large ({size_kb:.1f} KB > {settings.max_file_size_kb} KB limit)")

    content = base64.b64decode(file.content).decode("utf-8", errors="replace")
    return FileContent(path=path, branch=ref, size_kb=round(size_kb, 2), content=content)


def _list_repos(username: str, org: bool) -> list[RepoInfo]:
    client = get_github_client()
    try:
        source = client.get_organization(username) if org else client.get_user(username)
        repos = source.get_repos()
    except GithubException as e:
        raise GitHubClientError(f"Could not list repos for '{username}'", e.status) from e

    result = []
    for r in repos:
        result.append(RepoInfo(
            full_name=r.full_name,
            description=r.description,
            language=r.language,
            stars=r.stargazers_count,
            forks=r.forks_count,
            open_issues=r.open_issues_count,
            default_branch=r.default_branch,
            topics=r.get_topics(),
            visibility="private" if r.private else "public",
            created_at=r.created_at,
            updated_at=r.updated_at,
            url=r.html_url,
        ))
    return result




async def get_repo_info(owner: str, repo: str) -> RepoInfo:
    return await asyncio.to_thread(_fetch_repo_info, owner, repo)

async def get_repo_tree(owner: str, repo: str, branch: str | None = None, depth: int = 4) -> RepoTree:
    return await asyncio.to_thread(_fetch_repo_tree, owner, repo, branch, depth)

async def get_file_content(owner: str, repo: str, path: str, branch: str | None = None) -> FileContent:
    return await asyncio.to_thread(_fetch_file_content, owner, repo, path, branch)

async def list_repos(username: str, org: bool = False) -> list[RepoInfo]:
    return await asyncio.to_thread(_list_repos, username, org)
