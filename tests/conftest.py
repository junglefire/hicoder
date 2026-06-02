"""Shared test fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def tmp_config_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for test config files."""
    return tmp_path


@pytest.fixture
def sample_config_dict() -> dict:
    """Return a valid configuration dictionary."""
    return {
        "project": {
            "model": "gpt-4o",
            "provider": "openai",
            "api_key": "sk-test-key",
            "max_tokens": 4096,
        },
        "session": {
            "approval_policy": "auto",
            "sandbox_mode": "workspace-write",
        },
    }
