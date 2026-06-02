"""Tests for config loading and API key resolution."""

import os
from pathlib import Path

import pytest

from hicoder.config import Config, ConfigLoader
from hicoder.auth import ApiKeyError, resolve_api_key


class TestConfigDefaults:
    """Test built-in default config."""

    def test_defaults_only(self, tmp_path: Path) -> None:
        """With no user or project config, defaults are returned."""
        loader = ConfigLoader(
            cwd=tmp_path,
            hicoder_home=tmp_path / "nonexistent_hicoder_home",
        )
        config = loader.load()
        assert config.model == "gpt-4o"
        assert config.provider == "openai"
        assert config.max_tokens == 4096
        assert config.approval_policy == "auto"
        assert config.sandbox_mode == "workspace-write"


class TestThreeLayerMerge:
    """Test three-layer config loading and override."""

    def test_user_overrides_defaults(self, tmp_path: Path) -> None:
        """User config overrides built-in defaults."""
        user_home = tmp_path / "hicoder"
        user_home.mkdir()
        (user_home / "config.toml").write_text(
            '[project]\nmodel = "claude-sonnet-4-20250514"\nprovider = "anthropic"\n'
        )

        loader = ConfigLoader(
            cwd=tmp_path,
            hicoder_home=user_home,
        )
        config = loader.load()
        assert config.model == "claude-sonnet-4-20250514"
        assert config.provider == "anthropic"

    def test_project_overrides_user(self, tmp_path: Path) -> None:
        """Project config overrides user config."""
        user_home = tmp_path / "hicoder"
        user_home.mkdir()
        (user_home / "config.toml").write_text(
            '[project]\nmodel = "user-model"\n'
        )

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".hicoder" / "config.toml").parent.mkdir(exist_ok=True)
        (project_dir / ".hicoder" / "config.toml").write_text(
            '[project]\nmodel = "project-model"\n'
        )

        loader = ConfigLoader(
            cwd=project_dir,
            hicoder_home=user_home,
        )
        config = loader.load()
        assert config.model == "project-model"

    def test_custom_config_path(self, tmp_path: Path) -> None:
        """Custom config path replaces project config."""
        custom = tmp_path / "my-config.toml"
        custom.write_text('[project]\nmodel = "custom-model"\n')

        loader = ConfigLoader(
            cwd=tmp_path,
            hicoder_home=tmp_path / "nonexistent",
            custom_config_path=custom,
        )
        config = loader.load()
        assert config.model == "custom-model"

    def test_partial_override(self, tmp_path: Path) -> None:
        """Non-overridden fields retain their default values."""
        user_home = tmp_path / "hicoder"
        user_home.mkdir()
        (user_home / "config.toml").write_text(
            '[project]\nmodel = "custom-model"\n'
        )

        loader = ConfigLoader(
            cwd=tmp_path,
            hicoder_home=user_home,
        )
        config = loader.load()
        assert config.model == "custom-model"
        assert config.provider == "openai"  # default preserved
        assert config.max_tokens == 4096  # default preserved


class TestProviderValidation:
    """Test provider field validation."""

    def test_invalid_provider_raises(self, tmp_path: Path) -> None:
        """Invalid provider in config raises validation error."""
        user_home = tmp_path / "hicoder"
        user_home.mkdir()
        (user_home / "config.toml").write_text(
            '[project]\nprovider = "invalid"\n'
        )

        loader = ConfigLoader(
            cwd=tmp_path,
            hicoder_home=user_home,
        )
        with pytest.raises(Exception):  # pydantic.ValidationError
            loader.load()


class TestApiKeyResolution:
    """Test API key resolution from env vars and config."""

    def test_env_var_priority_openai(self) -> None:
        """OPENAI_API_KEY environment variable takes priority."""
        os.environ["__TEST_OPENAI_KEY"] = "env-key"
        try:
            # Simulate env var set
            os.environ["OPENAI_API_KEY"] = "env-key"
            result = resolve_api_key("openai", config_api_key="file-key")
            assert result == "env-key"
        finally:
            os.environ.pop("OPENAI_API_KEY", None)

    def test_env_var_priority_anthropic(self) -> None:
        """ANTHROPIC_API_KEY environment variable takes priority."""
        os.environ["ANTHROPIC_API_KEY"] = "anthropic-env-key"
        try:
            result = resolve_api_key("anthropic", config_api_key="file-key")
            assert result == "anthropic-env-key"
        finally:
            os.environ.pop("ANTHROPIC_API_KEY", None)

    def test_config_fallback(self) -> None:
        """Falls back to config key when env var not set."""
        # Ensure env vars are not set
        os.environ.pop("OPENAI_API_KEY", None)
        result = resolve_api_key("openai", config_api_key="file-key")
        assert result == "file-key"

    def test_missing_key_raises(self) -> None:
        """Missing key from both sources raises ApiKeyError."""
        os.environ.pop("OPENAI_API_KEY", None)
        with pytest.raises(ApiKeyError, match="OPENAI_API_KEY"):
            resolve_api_key("openai", config_api_key=None)

        os.environ.pop("ANTHROPIC_API_KEY", None)
        with pytest.raises(ApiKeyError, match="ANTHROPIC_API_KEY"):
            resolve_api_key("anthropic", config_api_key="")
