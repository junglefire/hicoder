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
    pass


def resolve_api_key(
    provider: Literal["openai", "anthropic"],
    config_api_key: str | None = None,
) -> str:
    """Resolve the API key for the given provider.

    Resolution order: env var → config file.
    Config supports "env:<VAR_NAME>" syntax for indirect env lookup.
    """
    env_var = _ENV_MAP.get(provider)
    if env_var:
        env_value = os.environ.get(env_var, "").strip()
        if env_value:
            return env_value

    if config_api_key:
        if config_api_key.startswith("env:"):
            var_name = config_api_key[len("env:"):].strip()
            if var_name:
                resolved = os.environ.get(var_name, "").strip()
                if resolved:
                    return resolved
        else:
            return config_api_key

    env_hint = f"{_ENV_MAP[provider]}" if provider in _ENV_MAP else f"{provider.upper()}_API_KEY"
    raise ApiKeyError(
        f"No API key found for provider '{provider}'. "
        f"Set the {env_hint} environment variable, or add "
        f"'api_key' to your config.toml (use 'env:<VAR_NAME>' to reference an env var)."
    )


def make_credential(
    provider: Literal["openai", "anthropic"],
    api_key: str,
):
    if provider == "openai":
        return OpenAICredential(api_key=api_key)
    elif provider == "anthropic":
        return AnthropicCredential(api_key=api_key)
    else:
        raise ValueError(f"Unknown provider: {provider}")
