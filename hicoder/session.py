"""Session: manages conversation state, tool registry, and configuration.

A Session represents a single chat session. It maintains the message history,
tool registry, and configuration snapshot. The agent_loop() function drives
the session forward.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path

from hicoder.config import Config
from hicoder.protocol import AgentMessage
from hicoder.tools import ToolRegistry


@dataclass
class Session:
    """Chat session state.

    Attributes:
        config: The loaded configuration snapshot.
        messages: Conversation history (system → user → assistant → tool).
        tool_registry: Registered tools with schema definitions.
        pending_input: Queue for mid-turn user messages (asyncio.Queue).
        cancel_event: Set to stop the agent loop gracefully.
    """

    config: Config
    messages: list[AgentMessage] = field(default_factory=list)
    tool_registry: ToolRegistry = field(default_factory=ToolRegistry)
    pending_input: asyncio.Queue[str] = field(default_factory=asyncio.Queue)
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)

    def receive_user_message(self, content: str) -> None:
        """Append a user message to the conversation history.

        Args:
            content: The user's text input.
        """
        self.messages.append(AgentMessage(role="user", content=content))

    def enqueue_pending_input(self, content: str) -> None:
        """Queue a user message for the next model call.

        Used for mid-turn interruption: the user sends a new message
        while tools are executing, and it gets appended before the next
        model call.

        Args:
            content: The user's text input.
        """
        self.pending_input.put_nowait(content)

    def drain_pending_inputs(self) -> list[AgentMessage]:
        """Drain all pending inputs and return as AgentMessages.

        Returns:
            List of new AgentMessage objects from the pending queue.
        """
        new_messages: list[AgentMessage] = []
        while not self.pending_input.empty():
            content = self.pending_input.get_nowait()
            new_messages.append(AgentMessage(role="user", content=content))
        return new_messages

    def get_history(self) -> list[AgentMessage]:
        """Return the full conversation history.

        Returns:
            List of AgentMessage objects in order.
        """
        return self.messages

    def append_assistant_message(self, content: str) -> None:
        """Append an assistant text message to history.

        Args:
            content: The assistant's text response.
        """
        self.messages.append(AgentMessage(role="assistant", content=content))

    def append_tool_result(self, tool_call_id: str, output: str) -> None:
        """Append a tool result message to history.

        Args:
            tool_call_id: The ID of the tool call this result belongs to.
            output: The tool's text output.
        """
        self.messages.append(
            AgentMessage(role="tool", content=output, tool_call_id=tool_call_id)
        )
