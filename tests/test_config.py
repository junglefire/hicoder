"""Tests for config loading and API key resolution."""

import json
import os
from pathlib import Path

import pytest

from hicoder.config import Config, load_config
from hicoder.auth import ApiKeyError, resolve_api_key


class TestLoadConfig:
    def test_minimal_config(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"model": "gpt-4o", "provider": "openai"}))
        cfg = load_config(path)
        assert cfg.model == "gpt-4o"
        assert cfg.provider == "openai"
        assert cfg.max_tokens == 4096
        assert cfg.approval_policy == "auto"
        assert cfg.sandbox_mode == "workspace-write"

    def test_full_config(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        data = {
            "model": "claude-sonnet-4-20250514",
            "provider": "anthropic",
            "api_key": "env:MY_KEY",
            "base_url": "https://example.com",
            "max_tokens": 2048,
            "approval_policy": "ask",
            "sandbox_mode": "readonly",
        }
        path.write_text(json.dumps(data))
        cfg = load_config(path)
        assert cfg.model == "claude-sonnet-4-20250514"
        assert cfg.provider == "anthropic"
        assert cfg.base_url == "https://example.com"
        assert cfg.max_tokens == 2048
        assert cfg.approval_policy == "ask"
        assert cfg.sandbox_mode == "readonly"

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "no-such-file.json")

    def test_invalid_provider_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"provider": "invalid"}))
        with pytest.raises(Exception):  # pydantic.ValidationError
            load_config(path)

    def test_partial_fields_keep_defaults(self, tmp_path: Path) -> None:
        path = tmp_path / "config.json"
        path.write_text(json.dumps({"model": "custom"}))
        cfg = load_config(path)
        assert cfg.model == "custom"
        assert cfg.provider == "openai"
        assert cfg.max_tokens == 4096


class TestApiKeyResolution:
    def test_env_var_priority_openai(self) -> None:
        os.environ["OPENAI_API_KEY"] = "env-key"
        try:
            result = resolve_api_key("openai", config_api_key="file-key")
            assert result == "env-key"
        finally:
            os.environ.pop("OPENAI_API_KEY", None)

    def test_env_var_priority_anthropic(self) -> None:
        os.environ["ANTHROPIC_API_KEY"] = "anthropic-env-key"
        try:
            result = resolve_api_key("anthropic", config_api_key="file-key")
            assert result == "anthropic-env-key"
        finally:
            os.environ.pop("ANTHROPIC_API_KEY", None)

    def test_config_fallback(self) -> None:
        os.environ.pop("OPENAI_API_KEY", None)
        result = resolve_api_key("openai", config_api_key="file-key")
        assert result == "file-key"

    def test_missing_key_raises(self) -> None:
        os.environ.pop("OPENAI_API_KEY", None)
        with pytest.raises(ApiKeyError, match="OPENAI_API_KEY"):
            resolve_api_key("openai", config_api_key=None)

        os.environ.pop("ANTHROPIC_API_KEY", None)
        with pytest.raises(ApiKeyError, match="ANTHROPIC_API_KEY"):
            resolve_api_key("anthropic", config_api_key="")

    def test_env_prefix_syntax(self) -> None:
        os.environ.pop("OPENAI_API_KEY", None)
        os.environ["MY_CUSTOM_KEY"] = "custom-value"
        try:
            result = resolve_api_key("openai", config_api_key="env:MY_CUSTOM_KEY")
            assert result == "custom-value"
        finally:
            os.environ.pop("MY_CUSTOM_KEY", None)

    def test_env_prefix_missing_var_raises(self) -> None:
        os.environ.pop("OPENAI_API_KEY", None)
        os.environ.pop("NONEXISTENT_KEY_123", None)
        with pytest.raises(ApiKeyError):
            resolve_api_key("openai", config_api_key="env:NONEXISTENT_KEY_123")
