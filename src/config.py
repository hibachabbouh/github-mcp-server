import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

env_path = Path(".env")
if env_path.exists():
    load_dotenv(env_path)
else:

    example_path = Path(".env.example")
    if example_path.exists():
        print(".env file not found. Using .env.example as fallback.")
        load_dotenv(example_path)
    else:
        print(" No .env or .env.example file found. Using environment variables.")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore", 
    )


    github_token: str = Field(
        default=os.getenv("GITHUB_TOKEN"),
        description="GitHub Personal Access Token"
    )
    groq_api_key: str = Field(
        default=os.getenv("GROQ_API_KEY"),
        description="Groq API key"
    )

    mcp_host: str = Field(
        default=os.getenv("MCP_HOST"),
        description="Host for MCP server"
    )
    mcp_port: int = Field(
        default=int(os.getenv("MCP_PORT")),
        description="Port for MCP server"
    )

    llm_model: str = Field(
        default=os.getenv("LLM_MODEL"),
        description="LLM model to use"
    )
    llm_max_tokens: int = Field(
        default=int(os.getenv("LLM_MAX_TOKENS")),
        description="Maximum tokens for LLM"
    )
    llm_temperature: float = Field(
        default=float(os.getenv("LLM_TEMPERATURE")),
        description="Temperature for LLM"
    )

    stale_branch_days: int = Field(
        default=int(os.getenv("STALE_BRANCH_DAYS")),
        description="Days after which a branch is considered stale"
    )
    max_file_size_kb: int = Field(
        default=int(os.getenv("MAX_FILE_SIZE_KB")),
        description="Maximum file size in KB to process"
    )
    max_repo_tree_depth: int = Field(
        default=int(os.getenv("MAX_REPO_TREE_DEPTH")),
        description="Maximum depth for repository tree traversal"
    )

   
    log_level: str = Field(
        default=os.getenv("LOG_LEVEL" ),
        description="Logging level"
    )



settings = Settings()


if settings.github_token and settings.groq_api_key:
    print("Configuration loaded successfully!")
else:
    print("Warning: Missing required environment variables (GITHUB_TOKEN or GROQ_API_KEY)")
    print("   Please check your .env file.")