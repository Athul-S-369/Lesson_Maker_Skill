import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

TARGET_MINUTES = 45
WORDS_PER_MINUTE = 130
APP_VERSION = "2.0"


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "").strip() or default)
    except ValueError:
        return default


def _float(name: str):
    try:
        return float(os.getenv(name, "").strip())
    except ValueError:
        return None


@dataclass
class Settings:
    anthropic_key: str
    tavily_key: str
    youtube_key: str
    books_key: str
    gen_model: str
    qc_model: str
    mock: bool
    failure_injection: bool
    data_dir: Path
    qc_provider: str          # "anthropic" (default) or "openai" (any OpenAI-compatible endpoint)
    openai_key: str
    openai_base: str
    llm_cache: bool           # disk cache for temperature-0 calls (cheap QC re-runs)
    stage_token_budget: int   # hard stop per pipeline stage (input + output tokens)
    price_in: float | None    # optional USD per million input tokens (cost shown only if both set)
    price_out: float | None
    rate_limit: int           # expensive POSTs per minute per client
    keyless_search: str       # "auto" (Bing only when no Tavily key), "1" (always) or "0" (off); Wikipedia is on unless "0"


def get_settings() -> Settings:
    anthropic = os.getenv("ANTHROPIC_API_KEY", "").strip()
    flag = os.getenv("MOCK_MODE", "").strip()
    mock = True if flag == "1" else False if flag == "0" else not anthropic
    data_dir = Path(os.getenv("DATA_DIR", "data"))
    if not data_dir.is_absolute():
        data_dir = ROOT / data_dir
    provider = os.getenv("QC_PROVIDER", "anthropic").strip().lower()
    return Settings(
        anthropic_key=anthropic,
        tavily_key=os.getenv("TAVILY_API_KEY", "").strip(),
        youtube_key=os.getenv("YOUTUBE_API_KEY", "").strip(),
        books_key=os.getenv("GOOGLE_BOOKS_API_KEY", "").strip(),
        gen_model=os.getenv("GEN_MODEL", "claude-sonnet-5-5"),
        qc_model=os.getenv("QC_MODEL", "claude-opus-5-5"),
        mock=mock,
        failure_injection=os.getenv("ENABLE_FAILURE_INJECTION", "0") == "1",
        data_dir=data_dir,
        qc_provider=provider if provider in ("anthropic", "openai") else "anthropic",
        openai_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_base=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/"),
        llm_cache=os.getenv("LLM_CACHE", "1") != "0",
        stage_token_budget=_int("STAGE_TOKEN_BUDGET", 400_000),
        price_in=_float("PRICE_IN_PER_MTOK"),
        price_out=_float("PRICE_OUT_PER_MTOK"),
        rate_limit=_int("RATE_LIMIT_PER_MIN", 60),
        keyless_search=os.getenv("KEYLESS_SEARCH", "auto").strip().lower() if os.getenv("KEYLESS_SEARCH", "auto").strip().lower() in ("auto", "1", "0") else "auto",
    )
