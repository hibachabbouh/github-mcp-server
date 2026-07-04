
import pytest
from src.llm import prompts


class TestPromptFormatting:
    def test_readme_analysis_user_formats_correctly(self):
        result = prompts.README_ANALYSIS_USER.format(
            full_name="hiba/test",
            language="Python",
            content="# My Project\n\nSome content here.",
        )
        assert "hiba/test" in result
        assert "Python" in result
        assert "# My Project" in result

    def test_readme_analysis_user_unknown_language(self):
        result = prompts.README_ANALYSIS_USER.format(
            full_name="hiba/test",
            language="unknown",
            content="minimal content",
        )
        assert "unknown" in result

    def test_issue_label_user_formats_correctly(self):
        issues_text = "#1: App crashes\n  Body: On login page\n#2: Add dark mode\n  Body: Feature request"
        result = prompts.ISSUE_LABEL_USER.format(
            full_name="hiba/test",
            issues_text=issues_text,
        )
        assert "hiba/test" in result
        assert "#1: App crashes" in result
        assert "#2: Add dark mode" in result

    def test_pr_review_user_formats_correctly(self):
        result = prompts.PR_REVIEW_USER.format(
            number=10, title="Add OAuth", author="hiba",
            additions=150, deletions=20, changed_files=5,
            head="feat/oauth", base="main",
            body="Implements OAuth2 login flow.",
            diff="[MODIFIED] src/auth.py  +120 -15",
        )
        assert "PR #10" in result
        assert "feat/oauth" in result
        assert "OAuth2 login" in result

    def test_pr_review_user_no_description(self):
        result = prompts.PR_REVIEW_USER.format(
            number=5, title="Quick fix", author="dev",
            additions=2, deletions=1, changed_files=1,
            head="fix/typo", base="main",
            body="(no description)",
            diff="[MODIFIED] README.md  +1 -0",
        )
        assert "(no description)" in result

    def test_branch_cleanup_user_formats_correctly(self):
        branches_text = "  - feat/old (last commit: 2024-01-01 by dev — old fix)"
        result = prompts.BRANCH_CLEANUP_USER.format(
            full_name="hiba/test",
            default_branch="main",
            days=30,
            branches_text=branches_text,
        )
        assert "hiba/test" in result
        assert "30" in result
        assert "feat/old" in result

    def test_repo_health_user_formats_correctly(self):
        result = prompts.REPO_HEALTH_USER.format(
            full_name="hiba/ai-coach",
            language="Python",
            stars=42, forks=5, open_issues=3, open_prs=1,
            visibility="public",
            topics="ai, mcp, langraph",
            updated_at="2025-06-01",
            total_commits=230,
            contributors="hiba, dev2",
            stale_count=2,
            has_readme=True,
            has_ci=True,
            has_license=True,
        )
        assert "hiba/ai-coach" in result
        assert "Python" in result
        assert "42" in result

    def test_all_system_prompts_contain_json_instruction(self):
       
        system_prompts = [
            prompts.README_ANALYSIS_SYSTEM,
            prompts.ISSUE_LABEL_SYSTEM,
            prompts.PR_REVIEW_SYSTEM,
            prompts.BRANCH_CLEANUP_SYSTEM,
            prompts.REPO_HEALTH_SYSTEM,
        ]
        for sp in system_prompts:
            assert "JSON" in sp, f"System prompt missing JSON instruction:\n{sp[:100]}"

    def test_system_prompts_forbid_markdown(self):
      
        system_prompts = [
            prompts.README_ANALYSIS_SYSTEM,
            prompts.ISSUE_LABEL_SYSTEM,
            prompts.PR_REVIEW_SYSTEM,
            prompts.BRANCH_CLEANUP_SYSTEM,
            prompts.REPO_HEALTH_SYSTEM,
        ]
        for sp in system_prompts:
            assert "markdown" in sp.lower() or "preamble" in sp.lower(), (
                f"System prompt doesn't forbid markdown/preamble:\n{sp[:100]}"
            )
