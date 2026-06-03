"""Configuration model."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class Config(BaseModel):
    model: str = Field(default="gpt-4o")
    provider: Literal["openai", "anthropic"] = Field(default="openai")
    api_key: str | None = Field(default=None)
    base_url: str | None = Field(default=None)
    max_tokens: int = Field(default=4096, gt=0)
    approval_policy: str = Field(default="auto")
    sandbox_mode: str = Field(default="workspace-write")


def load_config(path: Path) -> Config:
    """Load a TOML config file and return a Config instance.

    Raises FileNotFoundError if the file does not exist.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path) as f:
        data = json.load(f)

    return Config(**data)
