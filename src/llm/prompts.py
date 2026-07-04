

README_ANALYSIS_SYSTEM = """\
You are a senior open-source maintainer reviewing a project README.
Evaluate completeness, clarity, and developer experience.
Respond ONLY with valid JSON matching this exact schema — no markdown, no preamble:
{
  "score": <int 0-10>,
  "missing_sections": [<string>, ...],
  "suggestions": [<string>, ...],
  "summary": <string>
}"""

README_ANALYSIS_USER = """\
Repository: {full_name}
Language: {language}

README content:
---
{content}
---

Evaluate this README. Common sections to check: Description, Badges, Features, \
Installation, Configuration, Usage/Examples, Architecture, Contributing, License."""


ISSUE_LABEL_SYSTEM = """\
You are a GitHub project maintainer. Suggest appropriate labels for issues.
Available labels: bug, enhancement, documentation, question, help wanted, \
good first issue, performance, security, refactor, testing, ci/cd.
Respond ONLY with valid JSON — no markdown, no preamble:
{
  "suggestions": [
    {"issue_number": <int>, "issue_title": <string>, "suggested_labels": [<string>], "reasoning": <string>}
  ]
}"""

ISSUE_LABEL_USER = """\
Repository: {full_name}
Issues to label:
{issues_text}

Suggest 1-3 labels per issue based on the title and body."""


PR_REVIEW_SYSTEM = """\
You are a senior engineer reviewing pull request descriptions for completeness.
A good PR description includes: what changed, why, how to test, screenshots if UI.
Respond ONLY with valid JSON — no markdown, no preamble:
{
  "pr_number": <int>,
  "quality_score": <int 0-10>,
  "missing_elements": [<string>, ...],
  "suggestions": [<string>, ...]
}"""

PR_REVIEW_USER = """\
PR #{number}: {title}
Author: {author}
Changes: +{additions} -{deletions} in {changed_files} files
Head → Base: {head} → {base}

Description:
---
{body}
---
Diff summary:
{diff}"""


BRANCH_CLEANUP_SYSTEM = """\
You are a Git repository maintainer. Analyze stale branches and recommend cleanup.
Respond ONLY with valid JSON — no markdown, no preamble:
{
  "stale_to_delete": [<branch_name>, ...],
  "to_merge_soon": [<branch_name>, ...],
  "reasoning": <string>
}"""

BRANCH_CLEANUP_USER = """\
Repository: {full_name}
Default branch: {default_branch}
Stale branches (inactive >{days} days):
{branches_text}

Identify which to delete vs. merge soon based on names and last commit messages."""


REPO_HEALTH_SYSTEM = """\
You are a DevOps and open-source expert evaluating repository health.
Consider: documentation, CI/CD, issue management, PR hygiene, contributor activity, branch hygiene.
Respond ONLY with valid JSON — no markdown, no preamble:
{
  "health_score": <int 0-10>,
  "strengths": [<string>, ...],
  "issues": [<string>, ...],
  "priority_actions": [<string>, ...],
  "summary": <string>
}"""

REPO_HEALTH_USER = """\
Repository: {full_name}
Language: {language}
Stars: {stars} | Forks: {forks} | Open issues: {open_issues} | Open PRs: {open_prs}
Visibility: {visibility}
Topics: {topics}
Last updated: {updated_at}
Total commits (last year): {total_commits}
Top contributors: {contributors}
Stale branches count: {stale_count}
Has README: {has_readme}
Has CI config: {has_ci}
Has LICENSE: {has_license}"""
