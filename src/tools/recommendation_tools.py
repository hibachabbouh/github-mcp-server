from fastmcp import FastMCP

from src.config import settings
from src.github import branches, pull_requests, repositories, statistics
from src.llm import recommendations
from src.utils.exceptions import GitHubClientError, LLMError
from src.utils.logger import get_logger

logger = get_logger(__name__)


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    async def analyze_readme(owner: str, repo: str) -> dict:
        """Score the README completeness and get LLM-generated improvement suggestions.

        Args:
            owner: Repository owner.
            repo: Repository name.
        """
        try:
            info = await repositories.get_repo_info(owner, repo)
            file = await repositories.get_file_content(owner, repo, "README.md")
            result = await recommendations.analyze_readme(info.full_name, info.language, file.content)
            return result.model_dump()
        except (GitHubClientError, LLMError) as e:
            raise ValueError(str(e)) from e

    @mcp.tool()
    async def suggest_issue_labels(owner: str, repo: str, max_issues: int = 10) -> list[dict]:
        """Suggest GitHub labels for unlabeled open issues using LLM analysis.

        Args:
            owner: Repository owner.
            repo: Repository name.
            max_issues: Maximum number of issues to process (default 10).
        """
        try:
            from src.github import issues as issues_module
            all_issues = await issues_module.list_issues(owner, repo, state="open")
            unlabeled = [i for i in all_issues if not i.labels][:max_issues]
            if not unlabeled:
                return []
            issues_dicts = [i.model_dump(mode="json") for i in unlabeled]
            info = await repositories.get_repo_info(owner, repo)
            result = await recommendations.suggest_issue_labels(info.full_name, issues_dicts)
            return [r.model_dump() for r in result]
        except (GitHubClientError, LLMError) as e:
            raise ValueError(str(e)) from e

    @mcp.tool()
    async def review_pr_description(owner: str, repo: str, number: int) -> dict:
        """Evaluate a PR description for completeness and suggest improvements.

        Args:
            owner: Repository owner.
            repo: Repository name.
            number: PR number.
        """
        try:
            pr = await pull_requests.get_pull_request(owner, repo, number)
            diff = await pull_requests.get_pr_diff(owner, repo, number)
            result = await recommendations.review_pr_description(pr.model_dump(mode="json"), diff)
            return result.model_dump()
        except (GitHubClientError, LLMError) as e:
            raise ValueError(str(e)) from e

    @mcp.tool()
    async def generate_branch_cleanup_plan(owner: str, repo: str) -> dict:
        """Generate a prioritized plan to clean up stale branches using LLM analysis.

        Args:
            owner: Repository owner.
            repo: Repository name.
        """
        try:
            info = await repositories.get_repo_info(owner, repo)
            stale = await branches.detect_stale_branches(owner, repo)
            if not stale:
                return {"stale_to_delete": [], "to_merge_soon": [], "reasoning": "No stale branches found."}
            result = await recommendations.generate_branch_cleanup_plan(
                full_name=info.full_name,
                default_branch=info.default_branch,
                stale_days=settings.stale_branch_days,
                branches=[b.model_dump(mode="json") for b in stale],
            )
            return result.model_dump()
        except (GitHubClientError, LLMError) as e:
            raise ValueError(str(e)) from e

    @mcp.tool()
    async def summarize_repo_health(owner: str, repo: str) -> dict:
        """Generate an overall health report for a repository with priority action items.

        Args:
            owner: Repository owner.
            repo: Repository name.
        """
        try:
            info = await repositories.get_repo_info(owner, repo)
            stats = await statistics.get_repo_stats(owner, repo)
            stale = await branches.detect_stale_branches(owner, repo)

           
            has_readme = has_ci = has_license = False
            try:
                await repositories.get_file_content(owner, repo, "README.md")
                has_readme = True
            except Exception:
                pass
            try:
                await repositories.get_repo_tree(owner, repo, depth=2)
               
                tree = await repositories.get_repo_tree(owner, repo, depth=3)
                has_ci = any(".github/workflows" in n.path for n in tree.nodes)
                has_license = any("LICENSE" in n.path.upper() for n in tree.nodes)
            except Exception:
                pass

            repo_data = {
                "full_name": info.full_name,
                "language": info.language or "unknown",
                "stars": info.stars,
                "forks": info.forks,
                "open_issues": info.open_issues,
                "open_prs": stats.open_prs,
                "visibility": info.visibility,
                "topics": ", ".join(info.topics) or "none",
                "updated_at": str(info.updated_at),
                "total_commits": stats.total_commits_last_year,
                "contributors": ", ".join(c.login for c in stats.contributors[:5]),
                "stale_count": len(stale),
                "has_readme": has_readme,
                "has_ci": has_ci,
                "has_license": has_license,
            }
            result = await recommendations.summarize_repo_health(repo_data)
            return result.model_dump()
        except (GitHubClientError, LLMError) as e:
            raise ValueError(str(e)) from e
