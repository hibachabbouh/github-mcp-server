
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from src.models.schemas import (
    RepoInfo, BranchInfo, IssueInfo, PRInfo, PRReview,
    ReadmeAnalysis, IssueLabelSuggestion, PRDescriptionReview,
    BranchCleanupPlan, RepoHealthReport, FileNode, RepoTree,
)

NOW = datetime.now(timezone.utc)


class TestRepoInfo:
    def test_valid_public_repo(self):
        r = RepoInfo(
            full_name="hiba/test", description="desc", language="Python",
            stars=10, forks=2, open_issues=3, default_branch="main",
            topics=["mcp", "ai"], visibility="public",
            created_at=NOW, updated_at=NOW, url="https://github.com/hiba/test",
        )
        assert r.visibility == "public"
        assert r.topics == ["mcp", "ai"]

    def test_none_description_allowed(self):
        r = RepoInfo(
            full_name="hiba/test", description=None, language=None,
            stars=0, forks=0, open_issues=0, default_branch="main",
            topics=[], visibility="private",
            created_at=NOW, updated_at=NOW, url="https://github.com/hiba/test",
        )
        assert r.description is None
        assert r.language is None

    def test_model_dump_json_serializable(self):
        r = RepoInfo(
            full_name="hiba/test", description=None, language="Python",
            stars=5, forks=1, open_issues=0, default_branch="main",
            topics=[], visibility="public",
            created_at=NOW, updated_at=NOW, url="https://github.com/hiba/test",
        )
        data = r.model_dump(mode="json")
        assert isinstance(data["created_at"], str)
        assert "hiba/test" == data["full_name"]


class TestBranchInfo:
    def test_stale_flag_true(self):
        b = BranchInfo(
            name="feat/old", sha="abc123", protected=False,
            last_commit_date=NOW, last_commit_message="old fix",
            last_commit_author="dev", is_stale=True,
        )
        assert b.is_stale is True

    def test_default_not_stale(self):
        b = BranchInfo(
            name="main", sha="def456", protected=True,
            last_commit_date=NOW, last_commit_message="release",
            last_commit_author="hiba", 
        )
        assert b.is_stale is False

    def test_null_commit_fields_allowed(self):
        b = BranchInfo(
            name="empty-branch", sha="000", protected=False,
            last_commit_date=None, last_commit_message=None,
            last_commit_author=None,
        )
        assert b.last_commit_date is None


class TestIssueInfo:
    def test_valid_issue(self):
        i = IssueInfo(
            number=42, title="Bug in auth", state="open", body="Details here",
            labels=["bug"], assignees=["hiba"], created_at=NOW, updated_at=NOW,
            url="https://github.com/hiba/test/issues/42", comments=3,
        )
        assert i.number == 42
        assert "bug" in i.labels

    def test_empty_labels_and_assignees(self):
        i = IssueInfo(
            number=1, title="No labels", state="open", body=None,
            labels=[], assignees=[], created_at=NOW, updated_at=NOW,
            url="https://github.com/hiba/test/issues/1", comments=0,
        )
        assert i.labels == []
        assert i.assignees == []


class TestPRInfo:
    def test_valid_pr(self):
        pr = PRInfo(
            number=10, title="Add feature X", state="open", body="Description",
            author="hiba", base_branch="main", head_branch="feat/x",
            draft=False, mergeable=True, review_state="APPROVED",
            created_at=NOW, updated_at=NOW,
            url="https://github.com/hiba/test/pull/10",
            additions=50, deletions=10, changed_files=3,
        )
        assert pr.mergeable is True
        assert pr.review_state == "APPROVED"

    def test_draft_pr_null_mergeable(self):
        pr = PRInfo(
            number=99, title="WIP", state="open", body=None,
            author="dev", base_branch="main", head_branch="wip/feat",
            draft=True, mergeable=None, review_state=None,
            created_at=NOW, updated_at=NOW,
            url="https://github.com/hiba/test/pull/99",
            additions=0, deletions=0, changed_files=0,
        )
        assert pr.draft is True
        assert pr.mergeable is None


class TestLLMSchemas:
    def test_readme_analysis_score_bounds(self):
        r = ReadmeAnalysis(
            score=7, missing_sections=["Contributing"], suggestions=["Add badges"],
            summary="Good README, needs contribution guidelines.",
        )
        assert 0 <= r.score <= 10

    def test_readme_analysis_score_out_of_bounds(self):
        with pytest.raises(ValidationError):
            ReadmeAnalysis(score=11, missing_sections=[], suggestions=[], summary="x")

    def test_readme_analysis_score_negative(self):
        with pytest.raises(ValidationError):
            ReadmeAnalysis(score=-1, missing_sections=[], suggestions=[], summary="x")

    def test_issue_label_suggestion(self):
        s = IssueLabelSuggestion(
            issue_number=5, issue_title="App crashes on login",
            suggested_labels=["bug", "priority"],
            reasoning="Title mentions crash — likely a bug.",
        )
        assert len(s.suggested_labels) == 2

    def test_pr_description_review_score_bounds(self):
        r = PRDescriptionReview(
            pr_number=3, quality_score=5,
            missing_elements=["testing instructions"],
            suggestions=["Add steps to reproduce"],
        )
        assert r.quality_score == 5

    def test_branch_cleanup_plan(self):
        p = BranchCleanupPlan(
            stale_to_delete=["feat/old-login", "fix/typo-2022"],
            to_merge_soon=["feat/auth-refactor"],
            reasoning="feat/auth-refactor has recent commits and is close to main.",
        )
        assert "feat/old-login" in p.stale_to_delete

    def test_repo_health_report(self):
        h = RepoHealthReport(
            repo="hiba/test", health_score=8,
            strengths=["Good README", "CI configured"],
            issues=["No contributing guide"],
            priority_actions=["Add CONTRIBUTING.md"],
            summary="Healthy repo with minor gaps.",
        )
        assert h.health_score == 8

    def test_repo_health_score_out_of_bounds(self):
        with pytest.raises(ValidationError):
            RepoHealthReport(
                repo="hiba/test", health_score=11,
                strengths=[], issues=[], priority_actions=[], summary="x",
            )


class TestRepoTree:
    def test_tree_with_mixed_types(self):
        tree = RepoTree(
            full_name="hiba/test",
            branch="main",
            nodes=[
                FileNode(path="src", type="dir"),
                FileNode(path="src/main.py", type="file", size=1024),
                FileNode(path="README.md", type="file", size=512),
            ],
        )
        dirs = [n for n in tree.nodes if n.type == "dir"]
        files = [n for n in tree.nodes if n.type == "file"]
        assert len(dirs) == 1
        assert len(files) == 2
