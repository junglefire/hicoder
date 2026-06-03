"""HiCoder agent event types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class TokenUsage:
    """Token usage information from a model response."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    @property
    def input_tokens(self) -> int:
        return self.prompt_tokens

    @property
    def output_tokens(self) -> int:
        return self.completion_tokens


@dataclass
class AgentEvent:
    """Base class for all agent events."""

    type: str = field(default="agent_event", init=False)


@dataclass
class TextDelta(AgentEvent):
    """Incremental text chunk from the model."""

    type: Literal["text_delta"] = field(default="text_delta", init=False)
    text: str = ""


@dataclass
class ToolCall(AgentEvent):
    """Model requests a tool invocation (start of streaming)."""

    type: Literal["tool_call"] = field(default="tool_call", init=False)
    id: str = ""
    name: str = ""
    arguments: str = ""


@dataclass
class ToolCallDone(AgentEvent):
    """Model has finished providing arguments for a tool call."""

    type: Literal["tool_call_done"] = field(default="tool_call_done", init=False)
    id: str = ""
    name: str = ""
    arguments: str = ""


@dataclass
class TurnComplete(AgentEvent):
    """Model has finished a complete turn."""

    type: Literal["turn_complete"] = field(default="turn_complete", init=False)
    usage: TokenUsage = field(default_factory=TokenUsage)


@dataclass
class Error(AgentEvent):
    """An error occurred during model interaction."""

    type: Literal["error"] = field(default="error", init=False)
    message: str = ""
