import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel


def _clean_base_url(url: str | None) -> str | None:
    """Sanitize base_url by stripping trailing slashes and /chat/completions suffix."""
    if not url:
        return None
    cleaned = url.strip().rstrip("/")
    if cleaned.endswith("/chat/completions"):
        cleaned = cleaned[:-len("/chat/completions")].rstrip("/")
    return cleaned


def get_llm():
    """Return a LangChain ChatModel instance configured for the selected AI_PROVIDER."""
    provider = os.getenv("AI_PROVIDER", "gemini").strip().lower()

    if provider == "gemini":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            raise ImportError(
                "Package 'langchain-google-genai' is not installed. Run: pip install langchain-google-genai"
            )

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment (.env).")

        model = os.getenv("AI_MODEL") or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        return ChatGoogleGenerativeAI(model=model, google_api_key=api_key, temperature=0)

    elif provider in ("openai", "chatgpt"):
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "Package 'langchain-openai' is not installed. Run: pip install langchain-openai"
            )

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment (.env).")

        model = os.getenv("AI_MODEL", "gpt-4o-mini")
        base_url = _clean_base_url(os.getenv("AI_BASE_URL"))
        return ChatOpenAI(model=model, api_key=api_key, base_url=base_url, temperature=0)

    elif provider in ("anthropic", "claude"):
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError(
                "Package 'langchain-anthropic' is not installed. Run: pip install langchain-anthropic"
            )

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment (.env).")

        model = os.getenv("AI_MODEL", "claude-3-5-haiku-latest")
        base_url = _clean_base_url(os.getenv("AI_BASE_URL"))
        return ChatAnthropic(model=model, api_key=api_key, base_url=base_url, temperature=0)

    elif provider in ("custom", "openai-compatible"):
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "Package 'langchain-openai' is not installed. Run: pip install langchain-openai"
            )

        raw_base_url = os.getenv("AI_BASE_URL", "http://localhost:11434/v1")
        base_url = _clean_base_url(raw_base_url)
        api_key = os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY", "dummy-key")
        model = os.getenv("AI_MODEL", "llama3.1")
        return ChatOpenAI(model=model, api_key=api_key, base_url=base_url, temperature=0)

    else:
        raise ValueError(
            f"Unsupported AI_PROVIDER '{provider}'. Supported options: gemini | openai | anthropic | custom"
        )
