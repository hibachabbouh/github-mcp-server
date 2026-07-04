import json
from json_repair import repair_json

from src.llm import prompts
from src.llm.client import complete
from src.models.schemas import (
    ReadmeAnalysis, IssueLabelSuggestion, PRDescriptionReview,
    BranchCleanupPlan, RepoHealthReport,
)
from src.utils.exceptions import LLMError
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _parse_json(raw: str, context: str) -> dict:
    """Parse LLM output as JSON, repairing minor malformations."""
    try:
        return json.loads(repair_json(raw))
    except Exception as e:
        logger.error("JSON parse failed", context=context, raw=raw[:200])
        raise LLMError(f"LLM returned unparseable JSON for {context}: {e}") from e


async def analyze_readme(full_name: str, language: str | None, content: str) -> ReadmeAnalysis:
    user = prompts.README_ANALYSIS_USER.format(
        full_name=full_name, language=language or "unknown", content=content[:8000]
    )
    raw = await complete(prompts.README_ANALYSIS_SYSTEM, user)
    data = _parse_json(raw, "readme_analysis")
    return ReadmeAnalysis(**data)


async def suggest_issue_labels(full_name: str, issues: list[dict]) -> list[IssueLabelSuggestion]:
    issues_text = "\n".join(
        f"#{i['number']}: {i['title']}\n  Body: {(i.get('body') or '')[:300]}"
        for i in issues
    )
    user = prompts.ISSUE_LABEL_USER.format(full_name=full_name, issues_text=issues_text)
    raw = await complete(prompts.ISSUE_LABEL_SYSTEM, user)
    data = _parse_json(raw, "issue_labels")
    return [IssueLabelSuggestion(**s) for s in data.get("suggestions", [])]


async def review_pr_description(pr: dict, diff: str) -> PRDescriptionReview:
    user = prompts.PR_REVIEW_USER.format(
        number=pr["number"], title=pr["title"], author=pr["author"],
        additions=pr["additions"], deletions=pr["deletions"],
        changed_files=pr["changed_files"], head=pr["head_branch"],
        base=pr["base_branch"], body=pr.get("body") or "(no description)",
        diff=diff[:3000],
    )
    raw = await complete(prompts.PR_REVIEW_SYSTEM, user)
    data = _parse_json(raw, "pr_review")
    return PRDescriptionReview(**data)


async def generate_branch_cleanup_plan(
    full_name: str, default_branch: str, stale_days: int, branches: list[dict]
) -> BranchCleanupPlan:
    branches_text = "\n".join(
        f"  - {b['name']} (last commit: {b.get('last_commit_date', 'unknown')} "
        f"by {b.get('last_commit_author', '?')} — {b.get('last_commit_message', '')})"
        for b in branches
    )
    user = prompts.BRANCH_CLEANUP_USER.format(
        full_name=full_name, default_branch=default_branch,
        days=stale_days, branches_text=branches_text,
    )
    raw = await complete(prompts.BRANCH_CLEANUP_SYSTEM, user)
    data = _parse_json(raw, "branch_cleanup")
    return BranchCleanupPlan(**data)


async def summarize_repo_health(repo_data: dict) -> RepoHealthReport:
    user = prompts.REPO_HEALTH_USER.format(**repo_data)
    raw = await complete(prompts.REPO_HEALTH_SYSTEM, user)
    data = _parse_json(raw, "repo_health")
    return RepoHealthReport(repo=repo_data["full_name"], **data)
