"""Internal message model for HiCoder agent communication."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class AgentMessage:
    """A message in the agent conversation history.

    This is a lightweight representation used internally by HiCoder.
    It is converted to AgentScope Msg objects before sending to the model.
    """

    role: Literal["system", "user", "assistant", "tool"] = "user"
    content: str = ""
    tool_call_id: str | None = None
    """For tool role messages, the ID of the tool call this result belongs to."""
