import pytest
from unittest.mock import AsyncMock, patch
from src.llm.recommendations import (
    analyze_readme, suggest_issue_labels, review_pr_description,
    generate_branch_cleanup_plan, summarize_repo_health,
)
from src.utils.exceptions import LLMError


VALID_README_JSON = '''{
    "score": 7,
    "missing_sections": ["Contributing", "License"],
    "suggestions": ["Add badges", "Include architecture diagram"],
    "summary": "Good README with some gaps."
}'''

VALID_LABELS_JSON = '''{
    "suggestions": [
        {
            "issue_number": 1,
            "issue_title": "App crashes",
            "suggested_labels": ["bug"],
            "reasoning": "Crash = bug."
        }
    ]
}'''

VALID_PR_JSON = '''{
    "pr_number": 5,
    "quality_score": 6,
    "missing_elements": ["testing steps"],
    "suggestions": ["Add test instructions"]
}'''

VALID_BRANCH_JSON = '''{
    "stale_to_delete": ["feat/old-login"],
    "to_merge_soon": ["feat/auth-refactor"],
    "reasoning": "feat/auth-refactor is almost ready."
}'''

VALID_HEALTH_JSON = '''{
    "health_score": 8,
    "strengths": ["Good README", "CI present"],
    "issues": ["No contributing guide"],
    "priority_actions": ["Add CONTRIBUTING.md"],
    "summary": "Healthy repo with minor gaps."
}'''


@pytest.fixture
def mock_complete():
    with patch("src.llm.recommendations.complete") as mock:
        yield mock


class TestAnalyzeReadme:
    @pytest.mark.asyncio
    async def test_valid_response(self, mock_complete):
        mock_complete.return_value = VALID_README_JSON
        result = await analyze_readme("hiba/test", "Python", "# README\nsome content")
        assert result.score == 7
        assert "Contributing" in result.missing_sections
        assert len(result.suggestions) == 2

    @pytest.mark.asyncio
    async def test_malformed_json_repaired(self, mock_complete):
        # Missing closing brace — json-repair should handle this
        mock_complete.return_value = VALID_README_JSON.rstrip("}")
        result = await analyze_readme("hiba/test", "Python", "content")
        assert result.score == 7

    @pytest.mark.asyncio
    async def test_llm_error_propagates(self, mock_complete):
        mock_complete.side_effect = LLMError("Groq timeout")
        with pytest.raises(LLMError):
            await analyze_readme("hiba/test", "Python", "content")

    @pytest.mark.asyncio
    async def test_none_language_handled(self, mock_complete):
        mock_complete.return_value = VALID_README_JSON
        result = await analyze_readme("hiba/test", None, "content")
        assert result.score == 7


class TestSuggestIssueLabels:
    @pytest.mark.asyncio
    async def test_valid_response(self, mock_complete):
        mock_complete.return_value = VALID_LABELS_JSON
        issues = [{"number": 1, "title": "App crashes", "body": "On login"}]
        result = await suggest_issue_labels("hiba/test", issues)
        assert len(result) == 1
        assert result[0].issue_number == 1
        assert "bug" in result[0].suggested_labels

    @pytest.mark.asyncio
    async def test_empty_suggestions_list(self, mock_complete):
        mock_complete.return_value = '{"suggestions": []}'
        result = await suggest_issue_labels("hiba/test", [])
        assert result == []

    @pytest.mark.asyncio
    async def test_multiple_issues(self, mock_complete):
        multi_json = '''{
            "suggestions": [
                {"issue_number": 1, "issue_title": "Bug", "suggested_labels": ["bug"], "reasoning": "crash"},
                {"issue_number": 2, "issue_title": "Feature", "suggested_labels": ["enhancement"], "reasoning": "new feature"}
            ]
        }'''
        mock_complete.return_value = multi_json
        issues = [
            {"number": 1, "title": "Bug", "body": "crash"},
            {"number": 2, "title": "Feature", "body": "add dark mode"},
        ]
        result = await suggest_issue_labels("hiba/test", issues)
        assert len(result) == 2


class TestReviewPRDescription:
    @pytest.mark.asyncio
    async def test_valid_response(self, mock_complete):
        mock_complete.return_value = VALID_PR_JSON
        pr = {
            "number": 5, "title": "Add OAuth", "author": "hiba",
            "additions": 100, "deletions": 10, "changed_files": 4,
            "head_branch": "feat/oauth", "base_branch": "main",
            "body": "Implements OAuth.",
        }
        result = await review_pr_description(pr, "diff summary here")
        assert result.pr_number == 5
        assert result.quality_score == 6
        assert "testing steps" in result.missing_elements

    @pytest.mark.asyncio
    async def test_no_description_pr(self, mock_complete):
        mock_complete.return_value = VALID_PR_JSON
        pr = {
            "number": 5, "title": "Quick fix", "author": "dev",
            "additions": 1, "deletions": 0, "changed_files": 1,
            "head_branch": "fix/typo", "base_branch": "main",
            "body": None,
        }
        result = await review_pr_description(pr, "")
        assert result.quality_score == 6


class TestBranchCleanupPlan:
    @pytest.mark.asyncio
    async def test_valid_response(self, mock_complete):
        mock_complete.return_value = VALID_BRANCH_JSON
        branches = [
            {"name": "feat/old-login", "last_commit_date": "2024-01-01",
             "last_commit_author": "dev", "last_commit_message": "old stuff"},
        ]
        result = await generate_branch_cleanup_plan("hiba/test", "main", 30, branches)
        assert "feat/old-login" in result.stale_to_delete
        assert "feat/auth-refactor" in result.to_merge_soon

    @pytest.mark.asyncio
    async def test_all_delete_no_merge(self, mock_complete):
        mock_complete.return_value = '{"stale_to_delete": ["feat/a", "feat/b"], "to_merge_soon": [], "reasoning": "All abandoned."}'
        result = await generate_branch_cleanup_plan("hiba/test", "main", 30, [])
        assert len(result.stale_to_delete) == 2
        assert result.to_merge_soon == []


class TestRepoHealthReport:
    @pytest.mark.asyncio
    async def test_valid_response(self, mock_complete):
        mock_complete.return_value = VALID_HEALTH_JSON
        repo_data = {
            "full_name": "hiba/test", "language": "Python",
            "stars": 10, "forks": 2, "open_issues": 3, "open_prs": 1,
            "visibility": "public", "topics": "ai, mcp",
            "updated_at": "2025-06-01", "total_commits": 100,
            "contributors": "hiba", "stale_count": 1,
            "has_readme": True, "has_ci": True, "has_license": True,
        }
        result = await summarize_repo_health(repo_data)
        assert result.repo == "hiba/test"
        assert result.health_score == 8
        assert "Good README" in result.strengths

    @pytest.mark.asyncio
    async def test_llm_error_propagates(self, mock_complete):
        mock_complete.side_effect = LLMError("API down")
        with pytest.raises(LLMError):
            await summarize_repo_health({"full_name": "hiba/test", "language": "Python",
                "stars": 0, "forks": 0, "open_issues": 0, "open_prs": 0,
                "visibility": "public", "topics": "", "updated_at": "2025-01-01",
                "total_commits": 0, "contributors": "", "stale_count": 0,
                "has_readme": False, "has_ci": False, "has_license": False})
