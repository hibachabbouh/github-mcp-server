from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field




class RepoInfo(BaseModel):
    full_name: str
    description: str | None
    language: str | None
    stars: int
    forks: int
    open_issues: int
    default_branch: str
    topics: list[str]
    visibility: str
    created_at: datetime
    updated_at: datetime
    url: str


class FileNode(BaseModel):
    path: str
    type: str  
    size: int | None = None


class RepoTree(BaseModel):
    full_name: str
    branch: str
    nodes: list[FileNode]


class FileContent(BaseModel):
    path: str
    branch: str
    size_kb: float
    content: str
    encoding: str = "utf-8"



class BranchInfo(BaseModel):
    name: str
    sha: str
    protected: bool
    last_commit_date: datetime | None
    last_commit_message: str | None
    last_commit_author: str | None
    is_stale: bool = False


class BranchComparison(BaseModel):
    base: str
    head: str
    ahead_by: int
    behind_by: int
    files_changed: int
    additions: int
    deletions: int



class IssueInfo(BaseModel):
    number: int
    title: str
    state: str
    body: str | None
    labels: list[str]
    assignees: list[str]
    created_at: datetime
    updated_at: datetime
    url: str
    comments: int


class IssueComment(BaseModel):
    issue_number: int
    comment_id: int
    url: str



class PRInfo(BaseModel):
    number: int
    title: str
    state: str
    body: str | None
    author: str
    base_branch: str
    head_branch: str
    draft: bool
    mergeable: bool | None
    review_state: str | None
    created_at: datetime
    updated_at: datetime
    url: str
    additions: int
    deletions: int
    changed_files: int


class PRReview(BaseModel):
    reviewer: str
    state: str  # APPROVED | CHANGES_REQUESTED | COMMENTED
    submitted_at: datetime | None
    body: str | None



class ContributorStats(BaseModel):
    login: str
    commits: int
    additions: int
    deletions: int


class RepoStats(BaseModel):
    full_name: str
    total_commits_last_year: int
    contributors: list[ContributorStats]
    open_issues: int
    open_prs: int



class ReadmeAnalysis(BaseModel):
    score: int = Field(..., ge=0, le=10, description="Completeness score out of 10")
    missing_sections: list[str]
    suggestions: list[str]
    summary: str


class IssueLabelSuggestion(BaseModel):
    issue_number: int
    issue_title: str
    suggested_labels: list[str]
    reasoning: str


class PRDescriptionReview(BaseModel):
    pr_number: int
    quality_score: int = Field(..., ge=0, le=10)
    missing_elements: list[str]
    suggestions: list[str]


class BranchCleanupPlan(BaseModel):
    stale_to_delete: list[str]
    to_merge_soon: list[str]
    reasoning: str


class RepoHealthReport(BaseModel):
    repo: str
    health_score: int = Field(..., ge=0, le=10)
    strengths: list[str]
    issues: list[str]
    priority_actions: list[str]
    summary: str
