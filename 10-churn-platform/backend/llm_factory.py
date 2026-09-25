import os
import time
from typing import Any
from dotenv import load_dotenv
from flask import request
from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel

load_dotenv()


class TokenUsage(BaseModel):
    """Token consumption accounting."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def add(self, other: "TokenUsage") -> "TokenUsage":
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )


def _clean_base_url(url: str | None) -> str | None:
    """Sanitize base_url by stripping trailing slashes and /chat/completions suffix."""
    if not url:
        return None
    cleaned = url.strip().rstrip("/")
    if cleaned.endswith("/chat/completions"):
        cleaned = cleaned[:-len("/chat/completions")].rstrip("/")
    return cleaned


def extract_token_usage(raw_msg: Any) -> TokenUsage:
    """Extract prompt, completion, and total tokens from raw response."""
    p, c, t = 0, 0, 0
    if raw_msg is None:
        return TokenUsage()

    if hasattr(raw_msg, "usage_metadata") and raw_msg.usage_metadata:
        p = raw_msg.usage_metadata.get("input_tokens", 0) or 0
        c = raw_msg.usage_metadata.get("output_tokens", 0) or 0
        t = raw_msg.usage_metadata.get("total_tokens", 0) or (p + c)
    elif hasattr(raw_msg, "response_metadata") and raw_msg.response_metadata:
        u = raw_msg.response_metadata.get("token_usage") or raw_msg.response_metadata.get("usage") or {}
        p = u.get("prompt_tokens") or u.get("input_tokens", 0) or 0
        c = u.get("completion_tokens") or u.get("output_tokens", 0) or 0
        t = u.get("total_tokens") or (p + c)

    return TokenUsage(prompt_tokens=int(p), completion_tokens=int(c), total_tokens=int(t))


def get_llm_config_from_request(req=None) -> dict[str, Any]:
    """Extract AI model parameters prioritizing HTTP headers, then JSON body, then server .env."""
    r = req or request
    headers = getattr(r, "headers", {}) if r else {}
    body_config = {}
    if r and hasattr(r, "is_json") and r.is_json:
        try:
            body_config = (r.get_json(silent=True) or {}).get("model_config", {})
        except Exception:
            body_config = {}

    provider = (
        headers.get("x-ai-provider")
        or body_config.get("provider")
        or os.getenv("AI_PROVIDER", "custom")
    ).strip().lower()

    base_url = (
        headers.get("x-ai-base-url")
        or body_config.get("base_url")
        or os.getenv("AI_BASE_URL", "https://api.z.ai/api/coding/paas/v4")
    )

    api_key = (
        headers.get("x-ai-api-key")
        or body_config.get("api_key")
        or os.getenv("AI_API_KEY")
        or os.getenv("OPENAI_API_KEY", "")
    )

    model = (
        headers.get("x-ai-model")
        or body_config.get("model")
        or os.getenv("AI_MODEL", "GLM-5.3-Flash")
    )

    try:
        raw_temp = headers.get("x-ai-temperature") or body_config.get("temperature", 0.0)
        temperature = float(raw_temp)
    except (ValueError, TypeError):
        temperature = 0.0

    return {
        "provider": provider,
        "base_url": _clean_base_url(base_url),
        "api_key": api_key,
        "model": model,
        "temperature": temperature,
    }


def get_llm(req=None, override_config: dict[str, Any] | None = None, **override_kwargs) -> BaseChatModel:
    """Return configured BaseChatModel dynamically based on request parameters."""
    cfg = get_llm_config_from_request(req)
    if override_config:
        cfg.update(override_config)
    cfg.update(override_kwargs)
    provider = cfg["provider"]
    api_key = cfg["api_key"]
    model = cfg["model"]
    base_url = cfg["base_url"]
    temp = cfg.get("temperature", 0.0)

    if provider in ("custom", "openai-compatible", "z.ai", "zai"):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model,
            api_key=api_key or "dummy-key",
            base_url=base_url or "https://api.z.ai/api/coding/paas/v4",
            temperature=temp,
        )

    elif provider in ("openai", "chatgpt"):
        from langchain_openai import ChatOpenAI
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider.")
        return ChatOpenAI(
            model=model or "gpt-4o-mini",
            api_key=api_key,
            base_url=base_url,
            temperature=temp,
        )

    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for Google Gemini provider.")
        return ChatGoogleGenerativeAI(
            model=model or "gemini-2.5-flash",
            google_api_key=api_key,
            temperature=temp,
        )

    elif provider in ("anthropic", "claude"):
        from langchain_anthropic import ChatAnthropic
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider.")
        return ChatAnthropic(
            model=model or "claude-3-5-haiku-latest",
            api_key=api_key,
            base_url=base_url,
            temperature=temp,
        )

    else:
        # Fallback to OpenAI-compatible
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model,
            api_key=api_key or "dummy-key",
            base_url=base_url,
            temperature=temp,
        )


def test_llm_connection(config: dict[str, Any]) -> dict[str, Any]:
    """Test connection to the model endpoint and measure response latency."""
    t0 = time.time()
    try:
        llm = get_llm(override_config=config)
        resp = llm.invoke("Ping. Reply with exactly the single word 'PONG'.")
        latency_ms = int((time.time() - t0) * 1000)
        tokens = extract_token_usage(resp)
        return {
            "success": True,
            "message": f"Successfully connected to {config.get('model')} via {config.get('provider')}.",
            "latency_ms": latency_ms,
            "reply": str(resp.content)[:100],
            "token_usage": tokens.model_dump(),
        }
    except Exception as e:
        latency_ms = int((time.time() - t0) * 1000)
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}",
            "latency_ms": latency_ms,
            "reply": None,
            "token_usage": TokenUsage().model_dump(),
        }
