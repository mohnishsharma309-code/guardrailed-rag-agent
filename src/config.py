"""Settings loaded from environment (.env supported via app entrypoint)."""
import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    chroma_dir: str = os.getenv("CHROMA_DIR", "./.chroma")
    collection_name: str = os.getenv("COLLECTION_NAME", "meridian-docs")
    docs_dir: str = os.getenv("DOCS_DIR", "./data/docs")
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "600"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "120"))
    top_k: int = int(os.getenv("TOP_K", "4"))
    max_steps: int = int(os.getenv("MAX_STEPS", "6"))
    blocked_topics: list = field(
        default_factory=lambda: [
            t.strip().lower()
            for t in os.getenv("BLOCKED_TOPICS", "legal advice,medical advice").split(",")
            if t.strip()
        ]
    )


settings = Settings()


def require_api_key() -> None:
    if not settings.llm_api_key:
        raise RuntimeError(
            "LLM_API_KEY is not set. Copy .env.example to .env and add your key "
            "(any OpenAI-compatible endpoint works)."
        )
