"""API key resolution and authentication."""

from __future__ import annotations

import os
from typing import Literal

from agentscope.credential import (
    AnthropicCredential,
    OpenAICredential,
)


_ENV_MAP: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


class ApiKeyError(Exception):
    """Raised when no API key can be found."""


def resolve_api_key(
    provider: Literal["openai", "anthropic"],
    config_api_key: str | None = None,
) -> str:
    """Resolve the API key for the given provider.

    Resolution order:
    1. Environment variable (OPENAI_API_KEY / ANTHROPIC_API_KEY)
    2. config_api_key from loaded config file
    3. Raise ApiKeyError if neither is available

    Args:
        provider: The model provider ("openai" or "anthropic").
        config_api_key: API key from config file (may be empty string).

    Returns:
        The resolved API key string.

    Raises:
        ApiKeyError: If no key found from either source.
    """
    env_var = _ENV_MAP.get(provider)
    if env_var:
        env_value = os.environ.get(env_var, "").strip()
        if env_value:
            return env_value

    if config_api_key:
        return config_api_key

    env_hint = f"{_ENV_MAP[provider]}" if provider in _ENV_MAP else f"{provider.upper()}_API_KEY"
    raise ApiKeyError(
        f"No API key found for provider '{provider}'. "
        f"Set the {env_hint} environment variable, or add "
        f"'api_key' to your config.toml."
    )


def make_credential(
    provider: Literal["openai", "anthropic"],
    api_key: str,
):
    """Create an AgentScope credential for the given provider.

    Args:
        provider: The model provider.
        api_key: The resolved API key.

    Returns:
        An OpenAICredential or AnthropicCredential instance.
    """
    if provider == "openai":
        return OpenAICredential(api_key=api_key)
    elif provider == "anthropic":
        return AnthropicCredential(api_key=api_key)
    else:
        raise ValueError(f"Unknown provider: {provider}")
