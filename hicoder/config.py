"""Configuration loading and management."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError


class Config(BaseModel):
    """Top-level configuration for HiCoder.

    Fields map to the TOML structure:
        [project]  model, provider, api_key, max_tokens
        [session]  approval_policy, sandbox_mode
    """

    model: str = Field(default="gpt-4o")
    provider: Literal["openai", "anthropic"] = Field(default="openai")
    api_key: str | None = Field(default=None)
    max_tokens: int = Field(default=4096, gt=0)
    approval_policy: str = Field(default="auto")
    sandbox_mode: str = Field(default="workspace-write")
    cwd: Path = Field(default_factory=Path.cwd)
    hicoder_home: Path = Field(default_factory=lambda: Path.home() / ".hicoder")


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Shallow merge: override keys replace base keys."""
    result = base.copy()
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _dict_to_config(data: dict[str, Any]) -> Config:
    """Flatten nested TOML dict into Config fields."""
    flat: dict[str, Any] = {}
    for section in data.values():
        if isinstance(section, dict):
            flat.update(section)
    return Config(**flat)


class ConfigLoader:
    """Load configuration from three layers:
    1. Built-in defaults (config/default.toml in package)
    2. User config (~/.hicoder/config.toml)
    3. Project config (.hicoder/config.toml in cwd)

    Later layers override earlier ones.
    """

    def __init__(
        self,
        cwd: Path | None = None,
        hicoder_home: Path | None = None,
        custom_config_path: Path | None = None,
    ) -> None:
        self.cwd = cwd or Path.cwd()
        self.hicoder_home = hicoder_home or Path.home() / ".hicoder"
        self.custom_config_path = custom_config_path

    def _load_toml(self, path: Path) -> dict[str, Any]:
        """Read and parse a TOML file. Returns empty dict if missing."""
        if not path.is_file():
            return {}
        with open(path, "rb") as f:
            return tomllib.load(f)

    def _built_in_defaults(self) -> dict[str, Any]:
        """Layer 1: bundled config/default.toml."""
        defaults_path = Path(__file__).parent.parent / "config" / "default.toml"
        return self._load_toml(defaults_path)

    def _user_config(self) -> dict[str, Any]:
        """Layer 2: ~/.hicoder/config.toml."""
        return self._load_toml(self.hicoder_home / "config.toml")

    def _project_config(self) -> dict[str, Any]:
        """Layer 3: .hicoder/config.toml or custom path."""
        if self.custom_config_path:
            return self._load_toml(self.custom_config_path)
        return self._load_toml(self.cwd / ".hicoder" / "config.toml")

    def load(self) -> Config:
        """Load and merge all three config layers, return Config."""
        base = self._built_in_defaults()
        merged = _deep_merge(base, self._user_config())
        merged = _deep_merge(merged, self._project_config())

        config = _dict_to_config(merged)
        config.cwd = self.cwd
        config.hicoder_home = self.hicoder_home
        return config
