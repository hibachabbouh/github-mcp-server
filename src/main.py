"""
GitHub Repository Manager — MCP HTTP/SSE Server entry point.

Start with:
    python src/main.py
"""
from fastmcp import FastMCP

from src.config import settings
from src.utils.logger import setup_logging, get_logger
from src.tools import (
    repository_tools,
    branch_tools,
    issue_tools,
    pr_tools,
    recommendation_tools,
)

setup_logging()
logger = get_logger(__name__)

mcp = FastMCP(
    name="GitHub Repository Manager",
    instructions=(
        "You have access to a full suite of GitHub tools. "
        "Use repository tools to inspect structure and files, "
        "branch/issue/PR tools to manage the repository lifecycle, "
        "and recommendation tools (prefixed with analyze_, suggest_, review_, generate_, summarize_) "
        "to get LLM-powered improvement suggestions."
    ),
)


repository_tools.register(mcp)
branch_tools.register(mcp)
issue_tools.register(mcp)
pr_tools.register(mcp)
recommendation_tools.register(mcp)


def run() -> None:
    logger.info(
        "Starting GitHub MCP server",
        host=settings.mcp_host,
        port=settings.mcp_port,
        transport="http+sse",
    )
    mcp.run(
        transport="streamable-http",
        host=settings.mcp_host,
        port=settings.mcp_port,
    )


if __name__ == "__main__":
    run()
