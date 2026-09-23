from dataclasses import dataclass
import os


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


def _clean_base_url(url: str | None) -> str | None:
    """Sanitize base_url by removing trailing slashes and redundant /chat/completions suffix."""
    if not url:
        return None
    cleaned = url.strip().rstrip("/")
    if cleaned.endswith("/chat/completions"):
        cleaned = cleaned[:-len("/chat/completions")].rstrip("/")
    return cleaned


def generate_explanation(prompt: str) -> tuple[str, TokenUsage]:
    """Generate risk analysis narrative and return content alongside token usage statistics."""
    provider = os.getenv("AI_PROVIDER", "gemini").strip().lower()
    usage = TokenUsage()

    if provider == "gemini":
        try:
            from google import genai
        except ImportError:
            raise ImportError("Package 'google-genai' is not installed. Run: pip install google-genai")

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment (.env).")

        model = os.getenv("AI_MODEL") or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=model, contents=prompt)

        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage.prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
            usage.completion_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0
            usage.total_tokens = getattr(response.usage_metadata, "total_token_count", 0) or (
                usage.prompt_tokens + usage.completion_tokens
            )

        return (response.text or "").strip(), usage

    elif provider in ("openai", "chatgpt"):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Package 'openai' is not installed. Run: pip install openai")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment (.env).")

        base_url = _clean_base_url(os.getenv("AI_BASE_URL"))
        model = os.getenv("AI_MODEL", "gpt-4o-mini")
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )

        if hasattr(response, "usage") and response.usage:
            usage.prompt_tokens = getattr(response.usage, "prompt_tokens", 0) or 0
            usage.completion_tokens = getattr(response.usage, "completion_tokens", 0) or 0
            usage.total_tokens = getattr(response.usage, "total_tokens", 0) or (
                usage.prompt_tokens + usage.completion_tokens
            )

        return (response.choices[0].message.content or "").strip(), usage

    elif provider in ("anthropic", "claude"):
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("Package 'anthropic' is not installed. Run: pip install anthropic")

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment (.env).")

        base_url = _clean_base_url(os.getenv("AI_BASE_URL"))
        model = os.getenv("AI_MODEL", "claude-3-5-haiku-latest")
        client = Anthropic(api_key=api_key, base_url=base_url)
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        if hasattr(response, "usage") and response.usage:
            usage.prompt_tokens = getattr(response.usage, "input_tokens", 0) or 0
            usage.completion_tokens = getattr(response.usage, "output_tokens", 0) or 0
            usage.total_tokens = usage.prompt_tokens + usage.completion_tokens

        return response.content[0].text.strip(), usage

    elif provider in ("custom", "openai-compatible"):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Package 'openai' is not installed. Run: pip install openai")

        base_url = _clean_base_url(os.getenv("AI_BASE_URL", "http://localhost:11434/v1"))
        api_key = os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY", "dummy-key")
        model = os.getenv("AI_MODEL", "llama3.1")
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )

        if hasattr(response, "usage") and response.usage:
            usage.prompt_tokens = getattr(response.usage, "prompt_tokens", 0) or 0
            usage.completion_tokens = getattr(response.usage, "completion_tokens", 0) or 0
            usage.total_tokens = getattr(response.usage, "total_tokens", 0) or (
                usage.prompt_tokens + usage.completion_tokens
            )

        return (response.choices[0].message.content or "").strip(), usage

    else:
        raise ValueError(
            f"Unsupported AI_PROVIDER '{provider}'. Supported options: gemini | openai | anthropic | custom"
        )
