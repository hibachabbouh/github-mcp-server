
import os
import pytest
from unittest.mock import patch, AsyncMock

SKIP_REASON = "GITHUB_TOKEN not set — skipping e2e tests"
requires_token = pytest.mark.skipif(
    not os.environ.get("GITHUB_TOKEN"), reason=SKIP_REASON
)

OWNER = "octocat"
REPO = "Hello-World"

MOCK_README_RESULT = {
    "score": 5,
    "missing_sections": ["Installation", "Contributing"],
    "suggestions": ["Add installation steps", "Add contributing guide"],
    "summary": "Basic README missing key sections.",
}

MOCK_HEALTH_RESULT = {
    "health_score": 7,
    "strengths": ["Public repo", "Has branches"],
    "issues": ["Limited documentation"],
    "priority_actions": ["Add CONTRIBUTING.md"],
    "summary": "Healthy demo repo.",
}

MOCK_BRANCH_CLEANUP = {
    "stale_to_delete": [],
    "to_merge_soon": [],
    "reasoning": "No stale branches need cleanup.",
}


@requires_token
class TestRepositoryToolsE2E:
    @pytest.mark.asyncio
    async def test_list_repos_tool(self):
        from src.tools.repository_tools import register
        from fastmcp import FastMCP
        mcp = FastMCP("test")
        register(mcp)

        from src.github.repositories import list_repos
        result = await list_repos("octocat", org=False)
        assert len(result) > 0
        assert all(r.full_name.startswith("octocat/") for r in result)

    @pytest.mark.asyncio
    async def test_get_repo_info_tool(self):
        from src.github.repositories import get_repo_info
        result = await get_repo_info(OWNER, REPO)
        data = result.model_dump(mode="json")
        assert data["full_name"] == f"{OWNER}/{REPO}"
        assert isinstance(data["stars"], int)
        assert isinstance(data["topics"], list)

    @pytest.mark.asyncio
    async def test_get_repo_structure_tool(self):
        from src.github.repositories import get_repo_tree
        result = await get_repo_tree(OWNER, REPO, depth=2)
        data = result.model_dump(mode="json")
        assert data["full_name"] == f"{OWNER}/{REPO}"
        assert len(data["nodes"]) >= 1
        for node in data["nodes"]:
            assert node["path"].count("/") < 2


@requires_token
class TestBranchToolsE2E:
    @pytest.mark.asyncio
    async def test_list_branches_tool(self):
        from src.github.branches import list_branches
        result = await list_branches(OWNER, REPO)
        assert len(result) >= 1
        for b in result:
            assert b.sha is not None
            assert isinstance(b.protected, bool)

    @pytest.mark.asyncio
    async def test_compare_branches_tool(self):
        from src.github.branches import list_branches, compare_branches
        branches = await list_branches(OWNER, REPO)
        if len(branches) < 2:
            pytest.skip("Need at least 2 branches to compare")
        result = await compare_branches(OWNER, REPO, branches[0].name, branches[1].name)
        assert isinstance(result.ahead_by, int)
        assert isinstance(result.behind_by, int)


@requires_token
class TestRecommendationToolsE2E:
    """
    End-to-end tests for recommendation tools.
    Groq LLM is mocked — only GitHub calls are real.
    """

    @pytest.mark.asyncio
    async def test_analyze_readme_e2e(self):
        from src.llm.recommendations import analyze_readme as _analyze
        import json

        mock_response = json.dumps(MOCK_README_RESULT)

        with patch("src.llm.recommendations.complete", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response
            from src.github.repositories import get_repo_info, get_file_content
            try:
                info = await get_repo_info(OWNER, REPO)
                file = await get_file_content(OWNER, REPO, "README")
                content = file.content
            except Exception:
                # Hello-World may not have a README.md — use placeholder
                content = "# Hello World\nThis is a test repository."
                info = await get_repo_info(OWNER, REPO)

            result = await _analyze(info.full_name, info.language, content)
            assert 0 <= result.score <= 10
            assert isinstance(result.suggestions, list)

    @pytest.mark.asyncio
    async def test_summarize_repo_health_e2e(self):
        import json
        from src.github.repositories import get_repo_info, get_repo_tree
        from src.github.branches import detect_stale_branches
        from src.github.statistics import get_repo_stats

        mock_response = json.dumps(MOCK_HEALTH_RESULT)

        with patch("src.llm.recommendations.complete", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response

            info = await get_repo_info(OWNER, REPO)
            stats = await get_repo_stats(OWNER, REPO)
            stale = await detect_stale_branches(OWNER, REPO)

            repo_data = {
                "full_name": info.full_name,
                "language": info.language or "unknown",
                "stars": info.stars, "forks": info.forks,
                "open_issues": info.open_issues, "open_prs": stats.open_prs,
                "visibility": info.visibility, "topics": ", ".join(info.topics) or "none",
                "updated_at": str(info.updated_at), "total_commits": stats.total_commits_last_year,
                "contributors": ", ".join(c.login for c in stats.contributors[:5]),
                "stale_count": len(stale), "has_readme": True, "has_ci": False, "has_license": False,
            }

            from src.llm.recommendations import summarize_repo_health
            result = await summarize_repo_health(repo_data)
            assert result.repo == f"{OWNER}/{REPO}"
            assert 0 <= result.health_score <= 10

    @pytest.mark.asyncio
    async def test_generate_branch_cleanup_plan_e2e(self):
        import json
        from src.github.branches import detect_stale_branches
        from src.github.repositories import get_repo_info

        mock_response = json.dumps(MOCK_BRANCH_CLEANUP)

        with patch("src.llm.recommendations.complete", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_response

            info = await get_repo_info(OWNER, REPO)
            stale = await detect_stale_branches(OWNER, REPO)

            from src.llm.recommendations import generate_branch_cleanup_plan
            result = await generate_branch_cleanup_plan(
                full_name=info.full_name,
                default_branch=info.default_branch,
                stale_days=30,
                branches=[b.model_dump(mode="json") for b in stale],
            )
            assert isinstance(result.stale_to_delete, list)
            assert isinstance(result.to_merge_soon, list)
            assert isinstance(result.reasoning, str)
