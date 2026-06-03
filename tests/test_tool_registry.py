"""Tests for tool registry."""

import asyncio
import pytest

from agentscope.message import TextBlock, ToolResultState
from agentscope.tool._response import ToolResponse

from hicoder.tools.registry import (
    ToolRegistry,
    ToolResult,
    parallel_execute,
    _extract_output,
)
from hicoder.protocol import TextDelta, ToolCall, ToolCallDone, Error


class TestToolRegistry:
    """Test ToolRegistry registration and schema generation."""

    @pytest.mark.asyncio
    async def test_register_function(self) -> None:
        """Registering a function adds it to the registry."""
        registry = ToolRegistry()

        async def my_tool(x: int) -> ToolResponse:
            """My test tool.

            Args:
                x: A number.
            """
            return ToolResponse(content=[TextBlock(text=str(x))], state=ToolResultState.SUCCESS, is_last=True)

        tool = registry.register(my_tool)
        assert tool.name == "my_tool"
        assert tool.is_read_only is False

    @pytest.mark.asyncio
    async def test_register_with_custom_name(self) -> None:
        """Custom name overrides function name."""
        registry = ToolRegistry()

        async def internal_func() -> ToolResponse:
            """Internal func.

            """
            return ToolResponse(content=[TextBlock(text="ok")], state=ToolResultState.SUCCESS, is_last=True)

        tool = registry.register(internal_func, name="public_name")
        assert tool.name == "public_name"

    @pytest.mark.asyncio
    async def test_get_tool_definitions(self) -> None:
        """get_tool_definitions returns JSON Schema for registered tools."""
        registry = ToolRegistry()

        async def sample_tool(query: str) -> ToolResponse:
            """Search for something.

            Args:
                query: The search query.
            """
            return ToolResponse(content=[TextBlock(text=query)], state=ToolResultState.SUCCESS, is_last=True)

        registry.register(sample_tool)
        definitions = await registry.get_tool_definitions()

        assert isinstance(definitions, list)
        assert len(definitions) == 1
        assert "function" in definitions[0]
        assert definitions[0]["function"]["name"] == "sample_tool"

    @pytest.mark.asyncio
    async def test_multiple_tools_definitions(self) -> None:
        """Multiple tools generate multiple definitions."""
        registry = ToolRegistry()

        async def tool_a() -> ToolResponse:
            """Tool A."""
            return ToolResponse(content=[TextBlock(text="a")], state=ToolResultState.SUCCESS, is_last=True)

        async def tool_b(x: int) -> ToolResponse:
            """Tool B.

            Args:
                x: A number.
            """
            return ToolResponse(content=[TextBlock(text=str(x))], state=ToolResultState.SUCCESS, is_last=True)

        registry.register(tool_a)
        registry.register(tool_b)

        definitions = await registry.get_tool_definitions()
        assert len(definitions) == 2
        names = {d["function"]["name"] for d in definitions}
        assert names == {"tool_a", "tool_b"}


class TestToolExecution:
    """Test tool execution via registry."""

    @pytest.mark.asyncio
    async def test_execute_registered_tool(self) -> None:
        """Executing a registered tool returns events."""
        registry = ToolRegistry()

        async def echo(text: str) -> ToolResponse:
            """Echo text back.

            Args:
                text: Text to echo.
            """
            return ToolResponse(content=[TextBlock(text=text)], state=ToolResultState.SUCCESS, is_last=True)

        registry.register(echo)
        events = await registry.execute_tool_events("echo", {"text": "hello"})

        assert any(isinstance(e, ToolCall) for e in events)
        assert any(isinstance(e, TextDelta) for e in events)
        assert any(isinstance(e, ToolCallDone) for e in events)

        text_deltas = [e for e in events if isinstance(e, TextDelta)]
        assert len(text_deltas) == 1
        assert "hello" in text_deltas[0].text

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self) -> None:
        """Executing an unknown tool returns Error."""
        registry = ToolRegistry()
        events = await registry.execute_tool_events("nonexistent", {})

        assert len(events) == 1
        assert isinstance(events[0], Error)
        assert "nonexistent" in events[0].message

    @pytest.mark.asyncio
    async def test_execute_tool_error(self) -> None:
        """Tool execution error yields TextDelta with error message."""
        registry = ToolRegistry()

        async def failing_tool() -> ToolResponse:
            """A failing tool."""
            raise ValueError("something went wrong")

        registry.register(failing_tool)
        events = await registry.execute_tool_events("failing_tool", {})

        text_deltas = [e for e in events if isinstance(e, TextDelta)]
        assert len(text_deltas) == 1
        assert "Error" in text_deltas[0].text

    @pytest.mark.asyncio
    async def test_execute_batch_concurrent(self) -> None:
        """Batch execution runs all tools concurrently."""
        registry = ToolRegistry()

        async def quick_tool() -> ToolResponse:
            """A quick tool."""
            return ToolResponse(content=[TextBlock(text="done")], state=ToolResultState.SUCCESS, is_last=True)

        registry.register(quick_tool)
        results = await registry.execute_batch([
            ("quick_tool", {}, "call_1"),
            ("quick_tool", {}, "call_2"),
            ("quick_tool", {}, "call_3"),
        ])

        assert len(results) == 3
        for result_list in results:
            assert any(isinstance(e, ToolCall) for e in result_list)
            assert any(isinstance(e, ToolCallDone) for e in result_list)


class TestExtractOutput:
    """Test _extract_output helper."""

    def test_tool_response_with_text_blocks(self) -> None:
        result = ToolResponse(content=[TextBlock(text="hello")], state=ToolResultState.SUCCESS, is_last=True)
        assert _extract_output(result) == "hello"

    def test_string_result(self) -> None:
        assert _extract_output("direct string") == "direct string"

    def test_other_result(self) -> None:
        assert _extract_output(42) == "42"


class TestToolResult:
    """Test ToolResult dataclass."""

    def test_default_values(self) -> None:
        result = ToolResult(tool_call_id="call_1", output="ok")
        assert result.is_error is False
        assert result.diff is None

    def test_error_result(self) -> None:
        result = ToolResult(tool_call_id="call_1", output="error", is_error=True)
        assert result.is_error is True


class TestParallelExecute:
    """Test parallel_execute function."""

    @pytest.mark.asyncio
    async def test_parallel_execute_wrapper(self) -> None:
        """parallel_execute delegates to registry.execute_batch."""
        registry = ToolRegistry()

        async def test_tool() -> ToolResponse:
            """Test tool."""
            return ToolResponse(content=[TextBlock(text="ok")], state=ToolResultState.SUCCESS, is_last=True)

        registry.register(test_tool)
        coro = parallel_execute(registry, [("test_tool", {}, "call_1")])
        results = await coro

        assert len(results) == 1
