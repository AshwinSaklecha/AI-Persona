from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "Ashwin Persona API"
    environment: str = "development"
    app_debug: bool = Field(default=False, validation_alias="APP_DEBUG")
    api_prefix: str = "/api"

    llm_provider: str = Field(default="gemini", validation_alias="LLM_PROVIDER")
    llm_generation_max_attempts: int = Field(
        default=2,
        validation_alias="LLM_GENERATION_MAX_ATTEMPTS",
    )
    llm_generation_retry_base_delay_ms: int = Field(
        default=500,
        validation_alias="LLM_GENERATION_RETRY_BASE_DELAY_MS",
    )
    llm_temperature: float = Field(default=0.2, validation_alias="LLM_TEMPERATURE")
    llm_max_output_tokens: int = Field(
        default=700,
        validation_alias="LLM_MAX_OUTPUT_TOKENS",
    )

    gemini_api_key: str | None = Field(default=None, validation_alias="GEMINI_API_KEY")
    gemini_chat_model: str = "gemini-2.5-flash"
    gemini_chat_fallback_model: str | None = Field(
        default="gemini-2.5-flash-lite",
        validation_alias="GEMINI_CHAT_FALLBACK_MODEL",
    )
    gemini_embedding_model: str = "gemini-embedding-001"
    groq_api_key: str | None = Field(default=None, validation_alias="GROQ_API_KEY")
    groq_chat_model: str = Field(
        default="llama-3.3-70b-versatile",
        validation_alias="GROQ_CHAT_MODEL",
    )
    groq_chat_fallback_model: str | None = Field(
        default="llama-3.1-8b-instant",
        validation_alias="GROQ_CHAT_FALLBACK_MODEL",
    )
    groq_api_base_url: str = Field(
        default="https://api.groq.com/openai/v1",
        validation_alias="GROQ_API_BASE_URL",
    )

    github_username: str | None = Field(default=None, validation_alias="GITHUB_USERNAME")
    github_repos: str = Field(default="", validation_alias="GITHUB_REPOS")
    github_repo_readme_paths: str = Field(
        default="",
        validation_alias="GITHUB_REPO_README_PATHS",
    )
    github_contribution_repos: str = Field(
        default="deepchem/deepchem",
        validation_alias="GITHUB_CONTRIBUTION_REPOS",
    )
    github_token: str | None = Field(default=None, validation_alias="GITHUB_TOKEN")
    github_api_base_url: str = "https://api.github.com"

    retrieval_top_k: int = 5
    retrieval_min_score: float = 0.35
    chunk_size: int = 900
    chunk_overlap: int = 180
    allow_general_tech_answers: bool = Field(
        default=True,
        validation_alias="ALLOW_GENERAL_TECH_ANSWERS",
    )

    calcom_api_key: str | None = Field(default=None, validation_alias="CALCOM_API_KEY")
    calcom_username: str | None = Field(default=None, validation_alias="CALCOM_USERNAME")
    calcom_event_type: str | None = Field(default=None, validation_alias="CALCOM_EVENT_TYPE")
    calcom_api_base_url: str = "https://api.cal.com/v2"
    calcom_slots_api_version: str = "2024-09-04"
    calcom_bookings_api_version: str = "2024-08-13"
    timezone: str = Field(default="Asia/Kolkata", validation_alias="TIMEZONE")
    meeting_duration: int = Field(default=30, validation_alias="MEETING_DURATION")

    vapi_private_api_key: str | None = Field(default=None, validation_alias="VAPI_PRIVATE_API_KEY")
    vapi_assistant_id: str | None = Field(default=None, validation_alias="VAPI_ASSISTANT_ID")
    vapi_phone_number_id: str | None = Field(default=None, validation_alias="VAPI_PHONE_NUMBER_ID")
    vapi_shared_secret: str | None = Field(default=None, validation_alias="VAPI_SHARED_SECRET")
    public_backend_url: str | None = Field(default=None, validation_alias="PUBLIC_BACKEND_URL")
    vapi_api_base_url: str = "https://api.vapi.ai"

    frontend_origin: str = Field(
        default="http://localhost:3000",
        validation_alias="FRONTEND_ORIGIN",
    )
    next_public_api_base_url: str = Field(
        default="http://localhost:8000",
        validation_alias="NEXT_PUBLIC_API_BASE_URL",
    )

    data_dir: Path = ROOT_DIR / "data"
    source_dir: Path = ROOT_DIR / "data" / "sources"
    index_dir: Path = ROOT_DIR / "data" / "indexes"
    log_dir: Path = ROOT_DIR / "data" / "logs"
    index_name: str = "ashwin_persona"
    auto_rebuild_on_startup: bool = True

    model_config = SettingsConfigDict(
        env_file=(str(ROOT_DIR / ".env"), str(ROOT_DIR / "backend" / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    @property
    def index_metadata_path(self) -> Path:
        return self.index_dir / f"{self.index_name}.json"

    @property
    def index_faiss_path(self) -> Path:
        return self.index_dir / f"{self.index_name}.faiss"

    @property
    def index_numpy_path(self) -> Path:
        return self.index_dir / f"{self.index_name}.npy"

    @property
    def evaluation_log_path(self) -> Path:
        return self.log_dir / "events.jsonl"

    @property
    def debug(self) -> bool:
        return self.app_debug

    @property
    def github_source_dir(self) -> Path:
        return self.source_dir / "github" / "live"

    @property
    def github_repo_list(self) -> list[str]:
        return self._split_csv(self.github_repos)

    @property
    def github_contribution_repo_list(self) -> list[str]:
        return self._split_csv(self.github_contribution_repos)

    @property
    def github_repo_readme_path_map(self) -> dict[str, str]:
        mappings: dict[str, str] = {}
        for item in self._split_semicolon_csv(self.github_repo_readme_paths):
            if "=" not in item:
                continue
            repo_name, readme_path = item.split("=", 1)
            repo_name = repo_name.strip()
            readme_path = readme_path.strip().lstrip("/")
            if repo_name and readme_path:
                mappings[repo_name.lower()] = readme_path
        return mappings

    @staticmethod
    def _split_csv(value: str) -> list[str]:
        return [item.strip() for item in value.split(",") if item.strip()]

    @staticmethod
    def _split_semicolon_csv(value: str) -> list[str]:
        return [item.strip() for item in value.split(";") if item.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.index_dir.mkdir(parents=True, exist_ok=True)
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    settings.source_dir.mkdir(parents=True, exist_ok=True)
    settings.github_source_dir.mkdir(parents=True, exist_ok=True)
    return settings
