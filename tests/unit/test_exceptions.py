
import pytest
from src.utils.exceptions import GitHubClientError, LLMError, ToolInputError


class TestGitHubClientError:
    def test_message_stored(self):
        e = GitHubClientError("Repo not found", status_code=404)
        assert str(e) == "Repo not found"
        assert e.status_code == 404

    def test_no_status_code(self):
        e = GitHubClientError("Network error")
        assert e.status_code is None

    def test_is_exception(self):
        e = GitHubClientError("error")
        assert isinstance(e, Exception)

    def test_raise_and_catch(self):
        with pytest.raises(GitHubClientError) as exc_info:
            raise GitHubClientError("Rate limit exceeded", status_code=403)
        assert exc_info.value.status_code == 403

    def test_chained_exception(self):
        original = ValueError("original")
        try:
            raise GitHubClientError("Wrapped") from original
        except GitHubClientError as e:
            assert e.__cause__ is original


class TestLLMError:
    def test_basic(self):
        e = LLMError("Groq API timeout")
        assert str(e) == "Groq API timeout"
        assert isinstance(e, Exception)

    def test_raise_and_catch(self):
        with pytest.raises(LLMError):
            raise LLMError("Model overloaded")


class TestToolInputError:
    def test_basic(self):
        e = ToolInputError("File is a directory")
        assert str(e) == "File is a directory"

    def test_distinct_from_github_error(self):
        tool_err = ToolInputError("bad input")
        gh_err = GitHubClientError("api error")
        assert not isinstance(tool_err, GitHubClientError)
        assert not isinstance(gh_err, ToolInputError)

    def test_caught_by_base_exception(self):
        with pytest.raises(Exception):
            raise ToolInputError("something wrong")


class TestExceptionHierarchy:
    def test_github_error_not_llm_error(self):
        e = GitHubClientError("gh error")
        assert not isinstance(e, LLMError)

    def test_llm_error_not_tool_error(self):
        e = LLMError("llm error")
        assert not isinstance(e, ToolInputError)

    def test_all_are_exceptions(self):
        for cls in (GitHubClientError, LLMError, ToolInputError):
            assert issubclass(cls, Exception)
