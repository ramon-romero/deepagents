"""AWS Bedrock provider for deepagents-cli."""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_BEDROCK_MODEL = "bedrock:us.anthropic.claude-sonnet-4-5-20250929-v1:0"


@dataclass(frozen=True)
class BedrockEnv:
    """Parsed Bedrock environment configuration."""

    retry_mode: str
    max_attempts: int
    max_pool_connections: int
    requests_per_second: float | None
    max_bucket_size: float | None
    temperature: float | None
    max_tokens: int
    top_p: float | None
    top_k: int | None
    stop_sequences: list[str] | None
    thinking_enabled: bool
    thinking_budget: int


def _parse_int_env(var_name: str, default: int) -> int:
    value = os.environ.get(var_name)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _parse_optional_int_env(var_name: str) -> int | None:
    value = os.environ.get(var_name)
    if value is None or value.strip() == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _parse_float_env(var_name: str) -> float | None:
    value = os.environ.get(var_name)
    if value is None or value.strip() == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _parse_list_env(var_name: str) -> list[str] | None:
    value = os.environ.get(var_name)
    if value is None or value.strip() == "":
        return None
    value = value.strip()
    if value.startswith("["):
        import json

        try:
            data = json.loads(value)
        except json.JSONDecodeError:
            return None
        if isinstance(data, list) and all(isinstance(x, str) for x in data):
            return data
        return None
    if "|" in value:
        parts = [p.strip() for p in value.split("|") if p.strip()]
    else:
        parts = [p.strip() for p in value.split(",") if p.strip()]
    return parts or None


def _parse_bool_env(var_name: str) -> bool | None:
    value = os.environ.get(var_name)
    if value is None or value.strip() == "":
        return None
    value = value.strip().lower()
    if value in {"1", "true", "yes", "on", "enabled"}:
        return True
    if value in {"0", "false", "no", "off", "disabled"}:
        return False
    return None


def _normalize_model_id(model_name: str) -> str:
    model_id = model_name
    if model_id.lower().startswith("bedrock:"):
        model_id = model_id.split(":", 1)[1]
    return model_id


def _read_env() -> BedrockEnv:
    retry_mode = os.environ.get("BEDROCK_RETRY_MODE") or os.environ.get(
        "AWS_RETRY_MODE", "adaptive"
    )
    max_attempts = _parse_int_env(
        "BEDROCK_MAX_ATTEMPTS", _parse_int_env("AWS_MAX_ATTEMPTS", 3)
    )
    max_pool_connections = _parse_int_env("BEDROCK_MAX_POOL_CONNECTIONS", 10)
    requests_per_second = _parse_float_env("DEEPAGENTS_BEDROCK_RPS")
    max_bucket_size = _parse_float_env("DEEPAGENTS_BEDROCK_BURST")
    temperature = _parse_float_env("BEDROCK_TEMPERATURE")
    max_tokens = _parse_int_env("BEDROCK_MAX_TOKENS", 1024)
    top_p = _parse_float_env("BEDROCK_TOP_P")
    top_k = _parse_optional_int_env("BEDROCK_TOP_K")
    stop_sequences = _parse_list_env("BEDROCK_STOP")
    thinking_enabled = bool(_parse_bool_env("BEDROCK_THINKING"))
    thinking_budget = _parse_int_env("BEDROCK_THINKING_BUDGET", 4096)

    return BedrockEnv(
        retry_mode=retry_mode,
        max_attempts=max_attempts,
        max_pool_connections=max_pool_connections,
        requests_per_second=requests_per_second,
        max_bucket_size=max_bucket_size,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        top_k=top_k,
        stop_sequences=stop_sequences,
        thinking_enabled=thinking_enabled,
        thinking_budget=thinking_budget,
    )


def create_bedrock_model(model_name: str):
    """Create a Bedrock chat model using environment configuration."""
    from botocore.config import Config as BotocoreConfig
    from langchain_aws import ChatBedrock
    from langchain_core.rate_limiters import InMemoryRateLimiter

    env = _read_env()
    model_id = _normalize_model_id(model_name)

    temperature = env.temperature
    top_p = env.top_p
    top_k = env.top_k

    if temperature is None and top_p is None:
        temperature = 0.3
    if temperature is not None and top_p is not None:
        top_p = None
    if env.thinking_enabled:
        temperature = 1.0
        top_p = None
        top_k = None

    rate_limiter = None
    if env.requests_per_second is not None:
        rate_limiter = InMemoryRateLimiter(
            requests_per_second=env.requests_per_second,
            max_bucket_size=env.max_bucket_size or env.requests_per_second,
        )

    model_kwargs: dict[str, object] = {}
    if top_p is not None:
        model_kwargs["top_p"] = top_p
    if top_k is not None:
        model_kwargs["top_k"] = top_k
    if env.thinking_enabled:
        model_kwargs["thinking"] = {
            "type": "enabled",
            "budget_tokens": env.thinking_budget,
        }

    bedrock_config = BotocoreConfig(
        retries={"mode": env.retry_mode, "max_attempts": env.max_attempts},
        max_pool_connections=env.max_pool_connections,
    )

    return ChatBedrock(
        model_id=model_id,
        config=bedrock_config,
        rate_limiter=rate_limiter,
        temperature=temperature,
        max_tokens=env.max_tokens,
        stop=env.stop_sequences,
        model_kwargs=model_kwargs or None,
    )
