"""Tool registry: manages tool registration, schema generation, and execution.

Built on AgentScope's FunctionTool for schema generation from function
signatures. Execution is handled directly by calling the wrapped functions.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Callable

from agentscope.tool import FunctionTool

from hicoder.protocol import (
    AgentEvent,
    Error,
    TextDelta,
    ToolCall,
    ToolCallDone,
)


@dataclass
class ToolResult:
    """Result from a tool execution."""

    tool_call_id: str
    output: str
    is_error: bool = False
    diff: str | None = None
    """Unified diff of file changes, if applicable."""


class ToolRegistry:
    """Tool registry using AgentScope's FunctionTool for schema generation.

    Each registered function is wrapped in FunctionTool, which automatically
    extracts JSON Schema from the function's signature and docstring.
    Tool execution calls the function directly.
    """

    def __init__(self, cwd: str = "") -> None:
        self._tools: dict[str, FunctionTool] = {}
        self._cwd = cwd

    @property
    def cwd(self) -> str:
        return self._cwd

    def register(
        self,
        func: Callable,
        name: str | None = None,
        is_read_only: bool = False,
    ) -> FunctionTool:
        """Register a tool function.

        Args:
            func: Async or sync function to register.
            name: Custom tool name (defaults to func.__name__).
            is_read_only: Whether the tool is read-only.

        Returns:
            The created FunctionTool instance.
        """
        tool = FunctionTool(
            func=func,
            name=name,
            is_read_only=is_read_only,
        )
        self._tools[tool.name] = tool
        return tool

    async def get_tool_definitions(self) -> list[dict]:
        """Return OpenAI-compatible JSON Schema tool definitions.

        Uses FunctionTool's name, description, and input_schema attributes
        which are auto-generated from function signatures and docstrings.

        Returns:
            List of tool definition dicts in OpenAI function calling format.
        """
        definitions = []
        for tool in self._tools.values():
            definition = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                },
            }
            definitions.append(definition)
        return definitions

    async def execute_tool_events(
        self,
        name: str,
        args: dict[str, Any],
        tool_call_id: str = "",
    ) -> list[AgentEvent]:
        """Execute a registered tool, returning events.

        Wraps the tool execution result into HiCoder protocol events:
        ToolCall → TextDelta → ToolCallDone, or Error on failure.

        Args:
            name: Tool name to execute.
            args: Arguments to pass to the tool.
            tool_call_id: ID for tracing this tool call.

        Returns:
            List of AgentEvent objects.
        """
        if name not in self._tools:
            return [Error(message=f"Unknown tool: {name}")]

        events: list[AgentEvent] = []
        events.append(ToolCall(id=tool_call_id, name=name))

        try:
            tool = self._tools[name]
            result = await tool(**args)
            output_text = _extract_output(result)
            events.append(TextDelta(text=output_text))
        except Exception as e:
            output_text = f"Error executing {name}: {e}"
            events.append(TextDelta(text=output_text))

        events.append(ToolCallDone(id=tool_call_id, name=name))
        return events

    async def execute_batch(
        self,
        tool_calls: list[tuple[str, dict, str]],
    ) -> list[list[AgentEvent]]:
        """Execute multiple tool calls concurrently via asyncio.gather.

        Args:
            tool_calls: List of (tool_name, args, tool_call_id) tuples.

        Returns:
            List of event lists, one per tool call.
        """
        return await asyncio.gather(*[
            self.execute_tool_events(name, args, call_id)
            for name, args, call_id in tool_calls
        ])


def _extract_output(result) -> str:
    """Extract text output from a tool execution result."""
    from agentscope.tool._response import ToolResponse

    if isinstance(result, ToolResponse):
        parts = []
        for block in result.content:
            if hasattr(block, "text") and block.text:
                parts.append(block.text)
            elif hasattr(block, "__str__"):
                parts.append(str(block))
        return "\n".join(parts) if parts else str(result)
    if isinstance(result, str):
        return result
    return str(result)


def parallel_execute(
    registry: ToolRegistry,
    tool_calls: list[tuple[str, dict, str]],
):
    """Concurrent execution of multiple tool calls via asyncio.gather.

    Args:
        registry: The ToolRegistry instance.
        tool_calls: List of (tool_name, args, tool_call_id) tuples.

    Returns:
        Coroutine resolving to list of event lists.
    """
    return registry.execute_batch(tool_calls)
