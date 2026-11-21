"""Runtime settings, first-run prompt bootstrap, and environment checks."""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"
PROMPTS_TEMPLATE_DIR = BASE_DIR / "prompts.example"
OUTPUT_DIR = BASE_DIR / "output"

DEFAULT_PROVIDER = "ollama_cloud"
OLLAMA_DEFAULT_MODEL = "gpt-oss:20b-cloud"
OPENAI_DEFAULT_MODEL = "gpt-4o-mini"


def llm_provider() -> str:
    """Return the configured provider, defaulting to Ollama Cloud."""
    return os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER).strip().lower() or DEFAULT_PROVIDER


def ensure_prompts(
    prompts_dir: Path = PROMPTS_DIR,
    template_dir: Path = PROMPTS_TEMPLATE_DIR,
) -> bool:
    """Create prompts/ from prompts.example/ on first run.

    Returns True when templates were copied, False when prompts already exist.
    """
    if not template_dir.is_dir():
        if prompts_dir.is_dir() and any(prompts_dir.glob("*.py")):
            return False
        raise SystemExit(
            f"Missing prompt templates: {template_dir}. "
            "Restore the prompts.example/ directory."
        )

    prompts_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    for source in sorted(template_dir.glob("*.py")):
        target = prompts_dir / source.name
        if not target.exists():
            shutil.copy2(source, target)
            copied += 1

    if copied == 0:
        return False

    print(f"Created {prompts_dir.name}/ from {template_dir.name}/ ({copied} files).")
    print(f"Edit {prompts_dir.name}/ to customize the research methodology.")
    return True


def validate_environment() -> None:
    """Exit with one clear message when required keys are missing."""
    provider = llm_provider()
    missing = []
    if not os.getenv("EXA_API_KEY", "").strip():
        missing.append("EXA_API_KEY")

    if provider == "ollama_cloud":
        if not os.getenv("OLLAMA_API_KEY", "").strip():
            missing.append("OLLAMA_API_KEY")
    elif provider == "openai":
        if not os.getenv("OPENAI_API_KEY", "").strip():
            missing.append("OPENAI_API_KEY")
    else:
        raise SystemExit(
            f"Unsupported LLM_PROVIDER: {provider!r}. Use 'ollama_cloud' or 'openai'."
        )

    if missing:
        names = ", ".join(missing)
        raise SystemExit(
            f"Missing required environment variables: {names}. "
            "Add them to .env in the project root."
        )


def model_name() -> str:
    """Return the main LLM model for the selected provider."""
    if llm_provider() == "openai":
        return os.getenv("OPENAI_MODEL", OPENAI_DEFAULT_MODEL)
    return os.getenv("OLLAMA_MODEL", OLLAMA_DEFAULT_MODEL)


def llm_kwargs() -> dict:
    """Build CrewAI LLM kwargs for the selected provider."""
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    if llm_provider() == "openai":
        return {
            "model": model_name(),
            "temperature": temperature,
            "api_key": os.getenv("OPENAI_API_KEY"),
        }

    model = model_name()
    if not model.startswith("openai/"):
        model = f"openai/{model}"
    return {
        "model": model,
        "temperature": temperature,
        "base_url": os.getenv("LLM_BASE_URL", "https://ollama.com/v1"),
        "api_key": os.getenv("OLLAMA_API_KEY"),
    }


def extraction_config() -> dict:
    """Build OpenAI client config for page extraction on the selected provider."""
    if llm_provider() == "openai":
        return {
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "model": os.getenv("EXTRACTION_MODEL", OPENAI_DEFAULT_MODEL),
            "base_url": os.getenv("OPENAI_BASE_URL") or None,
        }
    return {
        "api_key": os.getenv("OLLAMA_API_KEY", ""),
        "model": os.getenv("EXTRACTION_MODEL", OLLAMA_DEFAULT_MODEL),
        "base_url": os.getenv("LLM_BASE_URL", "https://ollama.com/v1"),
    }


def provider_label() -> str:
    """Human-readable provider and model label."""
    return f"{llm_provider()} ({model_name()})"


def safe_report_name(brand_name: str) -> str:
    """Normalise a brand name for use in a report filename."""
    safe = re.sub(r"[^a-zA-Z0-9_-]", "_", brand_name).strip("_")
    return safe or "report"


def report_path(brand_name: str) -> Path:
    """Return the canonical report path for a brand name."""
    return OUTPUT_DIR / f"{safe_report_name(brand_name)}_market_research.md"
