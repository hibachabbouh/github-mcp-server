
import os
import pytest

SKIP_REASON = "GITHUB_TOKEN not set — skipping integration tests"
requires_token = pytest.mark.skipif(
    not os.environ.get("GITHUB_TOKEN"), reason=SKIP_REASON
)

OWNER = "octocat"
REPO = "Hello-World"


@requires_token
class TestRepoInfoIntegration:
    @pytest.mark.asyncio
    async def test_get_public_repo(self):
        from src.github.repositories import get_repo_info
        result = await get_repo_info(OWNER, REPO)
        assert result.full_name == f"{OWNER}/{REPO}"
        assert result.visibility == "public"
        assert result.stars >= 0

    @pytest.mark.asyncio
    async def test_nonexistent_repo_raises(self):
        from src.github.repositories import get_repo_info
        from src.utils.exceptions import GitHubClientError
        with pytest.raises(GitHubClientError) as exc_info:
            await get_repo_info("octocat", "this-repo-does-not-exist-xyz-999")
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_list_repos_for_user(self):
        from src.github.repositories import list_repos
        result = await list_repos("octocat", org=False)
        assert isinstance(result, list)
        assert len(result) > 0
        names = [r.full_name for r in result]
        assert f"{OWNER}/{REPO}" in names


@requires_token
class TestBranchesIntegration:
    @pytest.mark.asyncio
    async def test_list_branches(self):
        from src.github.branches import list_branches
        result = await list_branches(OWNER, REPO)
        assert isinstance(result, list)
        assert len(result) >= 1
        names = [b.name for b in result]
        assert "master" in names or "main" in names

    @pytest.mark.asyncio
    async def test_get_branch_info(self):
        from src.github.branches import list_branches, get_branch_info
        branches = await list_branches(OWNER, REPO)
        first = branches[0]
        info = await get_branch_info(OWNER, REPO, first.name)
        assert info.name == first.name
        assert info.sha is not None

    @pytest.mark.asyncio
    async def test_detect_stale_branches_returns_list(self):
        from src.github.branches import detect_stale_branches
        result = await detect_stale_branches(OWNER, REPO)
        assert isinstance(result, list)
        for b in result:
            assert b.is_stale is True


@requires_token
class TestRepoTreeIntegration:
    @pytest.mark.asyncio
    async def test_tree_depth_1(self):
        from src.github.repositories import get_repo_tree
        result = await get_repo_tree(OWNER, REPO, depth=1)
        assert result.full_name == f"{OWNER}/{REPO}"
        assert isinstance(result.nodes, list)
        
        for node in result.nodes:
            assert "/" not in node.path

    @pytest.mark.asyncio
    async def test_tree_default_depth(self):
        from src.github.repositories import get_repo_tree
        result = await get_repo_tree(OWNER, REPO)
        assert len(result.nodes) >= 1


@requires_token
class TestIssuesIntegration:
    @pytest.mark.asyncio
    async def test_list_open_issues(self):
        from src.github.issues import list_issues
        result = await list_issues(OWNER, REPO, state="open")
        assert isinstance(result, list)
        for issue in result:
            assert issue.state == "open"
            assert issue.number > 0

    @pytest.mark.asyncio
    async def test_list_closed_issues(self):
        from src.github.issues import list_issues
        result = await list_issues(OWNER, REPO, state="closed")
        assert isinstance(result, list)


@requires_token
class TestPRsIntegration:
    @pytest.mark.asyncio
    async def test_list_closed_prs(self):
        from src.github.pull_requests import list_pull_requests
        result = await list_pull_requests(OWNER, REPO, state="closed")
        assert isinstance(result, list)
        for pr in result:
            assert pr.number > 0
            assert pr.state == "closed"

    @pytest.mark.asyncio
    async def test_get_pr_diff(self):
        from src.github.pull_requests import list_pull_requests, get_pr_diff
        prs = await list_pull_requests(OWNER, REPO, state="closed")
        if not prs:
            pytest.skip("No closed PRs available to inspect")
        diff = await get_pr_diff(OWNER, REPO, prs[0].number)
        assert isinstance(diff, str)
        assert f"PR #{prs[0].number}" in diff


@requires_token
class TestStatsIntegration:
    @pytest.mark.asyncio
    async def test_get_repo_stats(self):
        from src.github.statistics import get_repo_stats
        result = await get_repo_stats(OWNER, REPO)
        assert result.full_name == f"{OWNER}/{REPO}"
        assert isinstance(result.contributors, list)
        assert result.total_commits_last_year >= 0
