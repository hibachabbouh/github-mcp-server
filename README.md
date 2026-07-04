# 🛠️ GitHub Repository Manager MCP

> **An MCP server that enables AI assistants to inspect, manage and improve GitHub repositories.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-1.x-6B46C1?style=flat)](https://modelcontextprotocol.io/)
[![FastMCP](https://img.shields.io/badge/FastMCP-HTTP%2FSSE-0EA5E9?style=flat)](https://github.com/jlowin/fastmcp)
[![Groq](https://img.shields.io/badge/LLM-Groq-F55036?style=flat)](https://groq.com/)
[![Tests](https://img.shields.io/badge/tests-76%20passed-22C55E?style=flat&logo=pytest)](https://docs.pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-22C55E?style=flat)](./LICENSE)

---

## What is this?

**GitHub Repository Manager MCP** is a [Model Context Protocol](https://modelcontextprotocol.io/) server that bridges AI assistants (Claude, etc.) with the GitHub API — and goes a step further with LLM-powered recommendations.

Instead of copy-pasting repo URLs and asking Claude to "review this code", you give your AI assistant **direct, structured access** to your repositories: it can browse structure, read issues, inspect pull requests, analyze branch health, and generate actionable improvement suggestions — all in a single conversation.

![Architecture Diagram](architecture/architecture.png)

---

## Features

### Repository Management
| Tool | Description |
|------|-------------|
| `list_repos` | List repositories for a user or organization |
| `get_repo_info` | Detailed metadata: stars, forks, language, topics |
| `get_repo_structure` | Browse directory tree up to configurable depth |
| `get_file_content` | Read any file from any branch |
| `get_repo_stats` | Commit frequency, contributor breakdown, code frequency |

###  Branch Management
| Tool | Description |
|------|-------------|
| `list_branches` | All branches with protection status |
| `get_branch_info` | Last commit, ahead/behind main, staleness indicator |
| `compare_branches` | Diff summary between two branches |
| `detect_stale_branches` | Branches inactive for N days |

### Issues
| Tool | Description |
|------|-------------|
| `list_issues` | Filter by state, label, assignee, milestone |
| `get_issue` | Full issue detail with comments |
| `create_issue` | Open a new issue programmatically |
| `add_issue_comment` | Comment on an existing issue |
| `close_issue` | Close with optional resolution comment |

### Pull Requests
| Tool | Description |
|------|-------------|
| `list_pull_requests` | Open/closed/merged PRs with filter |
| `get_pull_request` | Full PR detail with review status |
| `get_pr_diff` | Raw diff or file-by-file summary |
| `get_pr_reviews` | All reviews and their states |

###  LLM-Powered Recommendations 
| Tool | Description |
|------|-------------|
| `analyze_readme` | Score README completeness, suggest improvements |
| `suggest_issue_labels` | Auto-suggest labels for unlabeled issues |
| `review_pr_description` | Check PR description quality and coverage |
| `generate_branch_cleanup_plan` | Prioritized list of branches to delete or merge |
| `summarize_repo_health` | Overall repo health report with actionable next steps |

---

## Architecture

```
github-mcp-server/
│
├── src/
│   ├── main.py                  # FastMCP HTTP/SSE server entry point
│   ├── config.py                # Pydantic Settings — env vars
│   │
│   ├── github/
│   │   ├── client.py            # Authenticated PyGithub wrapper
│   │   ├── repositories.py      # Repo fetch + structure logic
│   │   ├── branches.py          # Branch queries + staleness detection
│   │   ├── issues.py            # Issue CRUD
│   │   ├── pull_requests.py     # PR queries + diff parsing
│   │   └── statistics.py        # Contributor + commit analytics
│   │
│   ├── llm/
│   │   ├── client.py            # Groq async client
│   │   ├── prompts.py           # Structured prompt templates
│   │   └── recommendations.py   # Recommendation orchestration
│   │
│   ├── tools/
│   │   ├── repository_tools.py  # MCP tool definitions — repos
│   │   ├── branch_tools.py      # MCP tool definitions — branches
│   │   ├── issue_tools.py       # MCP tool definitions — issues
│   │   ├── pr_tools.py          # MCP tool definitions — pull requests
│   │   └── recommendation_tools.py  # MCP tool definitions — LLM
│   │
│   ├── models/
│   │   └── schemas.py           # Pydantic models for all responses
│   │
│   └── utils/
│       ├── logger.py            # Structured logging (structlog)
│       └── exceptions.py        # Custom exceptions + MCP error mapping
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── screenshots/                 # Demo screenshots for README
├── README.md
├── ARCHITECTURE.md              # Design decisions + data flow
├── LICENSE
├── Dockerfile
├── pyproject.toml
├── .env.example
└── .gitignore
```

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Runtime | Python 3.11+ | Native `asyncio`, modern typing, stable base |
| MCP framework | [FastMCP](https://github.com/jlowin/fastmcp) | HTTP/SSE transport, minimal boilerplate |
| GitHub API | [PyGithub](https://pygithub.readthedocs.io/) | GitHub REST v3 access with Python objects |
| LLM provider | [Groq](https://groq.com/) | Fast async completions for repository recommendations |
| Prompt repair | [json-repair](https://pypi.org/project/json-repair/) | Recovers structured data from imperfect model output |
| Validation | [Pydantic v2](https://docs.pydantic.dev/) | Schema enforcement for tool inputs and outputs |
| Config | [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) | Typed `.env` loading and startup validation |
| Environment | [python-dotenv](https://pypi.org/project/python-dotenv/) | Local environment variable loading |
| Logging | [structlog](https://www.structlog.org/) | Structured logs that are easy to trace |
| Testing | [pytest](https://docs.pytest.org/) | Unit and integration test coverage |

### Screenshots

![Analyze README screenshot](screenshots/analyze_readme.png)
* analyze_readme

![Get repo info screenshot](screenshots/get_repo_info.png)
* get_repo_info

![Get repo structure screenshot](screenshots/get_repo_structure.png)
* get_repo_structure

![List branches screenshot](screenshots/list_branches.png)
* list_branches

---

## Quick Start

### Prerequisites
- Python 3.11+
- A [GitHub Personal Access Token](https://github.com/settings/tokens) (scopes: `repo`, `read:org`)
- A [Groq API key](https://console.groq.com/)

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/github-mcp-server.git
cd github-mcp-server

python -m venv .venv
source .venv/bin/activate      

pip install -e .
```

### Configuration

```bash
cp .env.example .env
```

```env
GITHUB_TOKEN=ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
GROQ_API_KEY=gsk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
MCP_HOST=0.0.0.0
MCP_PORT=8000
LLM_MODEL=llama-3.1-8b-instant
LLM_MAX_TOKENS=2048
LLM_TEMPERATURE=0.3
STALE_BRANCH_DAYS=30
MAX_FILE_SIZE_KB=500
MAX_REPO_TREE_DEPTH=4
LOG_LEVEL=INFO
```

### Run

```bash
python run.py
# Server running on http://0.0.0.0:8000/mcp
```

### Docker

```bash
docker build -t github-mcp-server .
docker run -p 8000:8000 --env-file .env github-mcp-server
```

---

## Connecting to Claude

### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "github-manager": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

### Claude.ai (Remote MCP)

Point your Claude.ai MCP settings to your publicly accessible server URL.

---

## Example Interactions

Once connected, you can ask Claude:

```
"List all open issues in myorg/myrepo and suggest appropriate labels for each."
```
```
"Which branches in hiba/portfolio-api haven't been touched in over 2 weeks?"
```
```
"Review the README of my latest repo and tell me what's missing."
```
```
"Summarize the health of myorg/backend-service and give me a priority action list."
```

---

## Running Tests

```bash
pytest tests/unit/ -v
pytest tests/integration/ -v --github-token=$GITHUB_TOKEN
```

---

## License

MIT — see [LICENSE](./LICENSE).

---

## Author

Hiba Chabbouh
Software Engineering Student @ INSAT

Interests:
- MLOps
- Generative AI
- LLM Systems
- Data Engineering
Contact:
- GitHub: [@hibachabbouh](https://github.com/hibachabbouh)
- LinkedIn: [Hiba Chabbouh](https://www.linkedin.com/in/hiba-chabbouh/)

