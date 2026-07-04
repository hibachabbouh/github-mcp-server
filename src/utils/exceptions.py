class GitHubClientError(Exception):
    """Raised when the GitHub API returns an error or is unreachable."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class LLMError(Exception):
    """Raised when the Groq API call fails."""


class ToolInputError(Exception):
    """Raised when tool arguments pass schema validation but fail business logic."""
