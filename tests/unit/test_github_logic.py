import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timezone, timedelta
import base64



NOW = datetime.now(timezone.utc)



def make_mock_repo(full_name="hiba/test", private=False, language="Python",
                   default_branch="main", stars=10, forks=2, issues=3):
    r = MagicMock()
    r.full_name = full_name
    r.description = "Test repo"
    r.language = language
    r.stargazers_count = stars
    r.forks_count = forks
    r.open_issues_count = issues
    r.default_branch = default_branch
    r.private = private
    r.get_topics.return_value = ["mcp", "ai"]
    r.created_at = NOW
    r.updated_at = NOW
    r.html_url = f"https://github.com/{full_name}"
    return r


def make_mock_branch(name="main", sha="abc123", protected=False, days_ago=5):
    b = MagicMock()
    b.name = name
    b.protected = protected
    commit = MagicMock()
    commit.sha = sha
    commit.commit.message = f"latest commit on {name}"
    commit.commit.author.date = datetime.now(timezone.utc) - timedelta(days=days_ago)
    commit.commit.author.name = "hiba"
    b.commit = commit
    return b


def make_mock_label(label_name: str) -> MagicMock:
   
    label = MagicMock(spec=[])  
    label.name = label_name
    return label


def make_mock_issue(number=1, title="Test issue", state="open",
                    label_names=None, assignee_logins=None, is_pr=False):
    i = MagicMock()
    i.number = number
    i.title = title
    i.state = state
    i.body = "Issue body"
    i.labels = [make_mock_label(l) for l in (label_names or [])]
    assignee_logins = assignee_logins or []
    assignees = []
    for login in assignee_logins:
        a = MagicMock(spec=[])
        a.login = login
        assignees.append(a)
    i.assignees = assignees
    i.created_at = NOW
    i.updated_at = NOW
    i.html_url = f"https://github.com/hiba/test/issues/{number}"
    i.comments = 0
    i.pull_request = MagicMock() if is_pr else None
    return i



class TestGetRepoInfo:
    @pytest.mark.asyncio
    async def test_public_repo_maps_correctly(self):
        mock_repo = make_mock_repo("hiba/test", private=False)
        with patch("src.github.repositories.get_github_client") as mock_client:
            mock_client.return_value.get_repo.return_value = mock_repo
            from src.github.repositories import get_repo_info
            result = await get_repo_info("hiba", "test")

        assert result.full_name == "hiba/test"
        assert result.visibility == "public"
        assert result.language == "Python"
        assert result.stars == 10
        assert "mcp" in result.topics

    @pytest.mark.asyncio
    async def test_private_repo_visibility(self):
        mock_repo = make_mock_repo("hiba/private-proj", private=True)
        with patch("src.github.repositories.get_github_client") as mock_client:
            mock_client.return_value.get_repo.return_value = mock_repo
            from src.github.repositories import get_repo_info
            result = await get_repo_info("hiba", "private-proj")

        assert result.visibility == "private"

    @pytest.mark.asyncio
    async def test_github_exception_raises_client_error(self):
        from github import GithubException
        from src.utils.exceptions import GitHubClientError
        with patch("src.github.repositories.get_github_client") as mock_client:
            mock_client.return_value.get_repo.side_effect = GithubException(404, "Not Found")
            from src.github.repositories import get_repo_info
            with pytest.raises(GitHubClientError) as exc_info:
                await get_repo_info("hiba", "nonexistent")
        assert exc_info.value.status_code == 404


class TestGetFileContent:
    @pytest.mark.asyncio
    async def test_file_content_decoded(self):
        mock_repo = make_mock_repo()
        mock_file = MagicMock()
        mock_file.size = 512
        raw = b"# Hello World\n\nThis is a README."
        mock_file.content = base64.b64encode(raw).decode()
        mock_repo.get_contents.return_value = mock_file

        with patch("src.github.repositories.get_github_client") as mock_client:
            mock_client.return_value.get_repo.return_value = mock_repo
            from src.github.repositories import get_file_content
            result = await get_file_content("hiba", "test", "README.md")

        assert "Hello World" in result.content
        assert result.path == "README.md"

    @pytest.mark.asyncio
    async def test_directory_raises_tool_input_error(self):
        from src.utils.exceptions import ToolInputError
        mock_repo = make_mock_repo()
        mock_repo.get_contents.return_value = [MagicMock(), MagicMock()]

        with patch("src.github.repositories.get_github_client") as mock_client:
            mock_client.return_value.get_repo.return_value = mock_repo
            from src.github.repositories import get_file_content
            with pytest.raises(ToolInputError):
                await get_file_content("hiba", "test", "src/")

    @pytest.mark.asyncio
    async def test_file_too_large_raises_tool_input_error(self):
        from src.utils.exceptions import ToolInputError
        mock_repo = make_mock_repo()
        mock_file = MagicMock()
        mock_file.size = 600 * 1024  # 600 KB > 500 KB limit
        mock_file.content = base64.b64encode(b"x" * 100).decode()
        mock_repo.get_contents.return_value = mock_file

        with patch("src.github.repositories.get_github_client") as mock_client:
            mock_client.return_value.get_repo.return_value = mock_repo
            from src.github.repositories import get_file_content
            with pytest.raises(ToolInputError, match="too large"):
                await get_file_content("hiba", "test", "huge_file.bin")


class TestGetRepoTree:
    @pytest.mark.asyncio
    async def test_depth_filtering(self):
        """
        depth=N excludes paths with >= N slashes.
        depth=3 → includes paths with 0, 1, 2 slashes; excludes 3+.
        
        src                    → 0 slashes → included
        src/main.py            → 1 slash   → included
        src/utils/helper.py    → 2 slashes → included
        src/utils/nested/deep  → 3 slashes → excluded
        """
        mock_repo = make_mock_repo()

        def make_tree_item(path, type_, size=None):
            item = MagicMock()
            item.path = path
            item.type = type_
            item.size = size
            return item

        mock_tree = MagicMock()
        mock_tree.tree = [
            make_tree_item("src", "tree"),
            make_tree_item("src/main.py", "blob", 1024),
            make_tree_item("src/utils/helper.py", "blob", 512),
            make_tree_item("src/utils/nested/deep.py", "blob", 256),
        ]
        mock_repo.get_git_tree.return_value = mock_tree

        with patch("src.github.repositories.get_github_client") as mock_client:
            mock_client.return_value.get_repo.return_value = mock_repo
            from src.github.repositories import get_repo_tree
            result = await get_repo_tree("hiba", "test", depth=3)

        paths = [n.path for n in result.nodes]
        assert "src" in paths
        assert "src/main.py" in paths
        assert "src/utils/helper.py" in paths
        assert "src/utils/nested/deep.py" not in paths

    @pytest.mark.asyncio
    async def test_depth_1_only_root(self):
        mock_repo = make_mock_repo()
        mock_tree = MagicMock()
        item_root = MagicMock(); item_root.path = "README.md"; item_root.type = "blob"; item_root.size = 200
        item_nested = MagicMock(); item_nested.path = "src/main.py"; item_nested.type = "blob"; item_nested.size = 100
        mock_tree.tree = [item_root, item_nested]
        mock_repo.get_git_tree.return_value = mock_tree

        with patch("src.github.repositories.get_github_client") as mock_client:
            mock_client.return_value.get_repo.return_value = mock_repo
            from src.github.repositories import get_repo_tree
            result = await get_repo_tree("hiba", "test", depth=1)

        paths = [n.path for n in result.nodes]
        assert "README.md" in paths
        assert "src/main.py" not in paths



class TestListBranches:
    @pytest.mark.asyncio
    async def test_stale_flag_set_correctly(self):
        mock_repo = make_mock_repo()
        fresh = make_mock_branch("main", days_ago=2)
        stale = make_mock_branch("feat/old", days_ago=45)
        mock_repo.get_branches.return_value = [fresh, stale]

        with patch("src.github.branches.get_github_client") as mock_client:
            mock_client.return_value.get_repo.return_value = mock_repo
            from src.github.branches import list_branches
            result = await list_branches("hiba", "test")

        assert result[0].name == "main"
        assert result[0].is_stale is False
        assert result[1].name == "feat/old"
        assert result[1].is_stale is True

    @pytest.mark.asyncio
    async def test_detect_stale_filters_correctly(self):
        mock_repo = make_mock_repo()
        branches_mock = [
            make_mock_branch("main", days_ago=1),
            make_mock_branch("feat/stale-a", days_ago=60),
            make_mock_branch("feat/stale-b", days_ago=90),
            make_mock_branch("feat/active", days_ago=10),
        ]
        mock_repo.get_branches.return_value = branches_mock

        with patch("src.github.branches.get_github_client") as mock_client:
            mock_client.return_value.get_repo.return_value = mock_repo
            from src.github.branches import detect_stale_branches
            result = await detect_stale_branches("hiba", "test")

        stale_names = [b.name for b in result]
        assert "feat/stale-a" in stale_names
        assert "feat/stale-b" in stale_names
        assert "main" not in stale_names
        assert "feat/active" not in stale_names
        assert len(result) == 2



class TestIssues:
    @pytest.mark.asyncio
    async def test_prs_excluded_from_issues(self):
        mock_repo = make_mock_repo()
        real_issue = make_mock_issue(1, "Real issue", is_pr=False)
        pr_as_issue = make_mock_issue(2, "PR showing as issue", is_pr=True)
        mock_repo.get_issues.return_value = [real_issue, pr_as_issue]

        with patch("src.github.issues.get_github_client") as mock_client:
            mock_client.return_value.get_repo.return_value = mock_repo
            from src.github.issues import list_issues
            result = await list_issues("hiba", "test")

        assert len(result) == 1
        assert result[0].number == 1

    @pytest.mark.asyncio
    async def test_label_names_extracted(self):
        mock_repo = make_mock_repo()
        issue = make_mock_issue(1, label_names=["bug", "priority"])
        mock_repo.get_issues.return_value = [issue]

        with patch("src.github.issues.get_github_client") as mock_client:
            mock_client.return_value.get_repo.return_value = mock_repo
            from src.github.issues import list_issues
            result = await list_issues("hiba", "test")

        assert "bug" in result[0].labels
        assert "priority" in result[0].labels

    @pytest.mark.asyncio
    async def test_empty_issue_list(self):
        mock_repo = make_mock_repo()
        mock_repo.get_issues.return_value = []

        with patch("src.github.issues.get_github_client") as mock_client:
            mock_client.return_value.get_repo.return_value = mock_repo
            from src.github.issues import list_issues
            result = await list_issues("hiba", "test")

        assert result == []
