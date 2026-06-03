"""Integration tests for agent_loop."""

import asyncio
import json

import pytest

from agentscope.credential import OpenAICredential
from agentscope.message import TextBlock, ToolCallBlock
from agentscope.model import ChatModelBase, ChatResponse, ChatUsage
from agentscope.message import ToolResultState
from agentscope.tool._response import ToolResponse

from hicoder.agent_loop import agent_loop, _is_retryable
from hicoder.config import Config
from hicoder.models.model_client import ModelClient
from hicoder.protocol import AgentMessage, Error, TextDelta, ToolCall, TurnComplete
from hicoder.session import Session
from hicoder.tools import ToolRegistry


class _StreamingFakeModel(ChatModelBase):
    """Fake model that streams predefined ChatResponse chunks."""

    class Parameters(ChatModelBase.Parameters):
        pass

    def __init__(self, chunk_sequences: list[list[ChatResponse]]) -> None:
        self._chunk_sequences = chunk_sequences
        self._call_count = 0
        cred = OpenAICredential(api_key="fake-key")
        super().__init__(
            credential=cred,
            model="fake-model",
            parameters=self.Parameters(),
            stream=True,
            max_retries=0,
        )

    async def _call_api(self, model_name, messages, tools=None, tool_choice=None, **kwargs):
        idx = self._call_count
        self._call_count += 1

        if idx >= len(self._chunk_sequences):
            chunks = []
        else:
            chunks = self._chunk_sequences[idx]

        async def gen():
            for chunk in chunks:
                yield chunk

        return gen()


def _make_config() -> Config:
    return Config(model="fake", provider="openai", api_key="fake", cwd="/tmp")


def _make_session(config: Config | None = None) -> Session:
    if config is None:
        config = _make_config()
    registry = ToolRegistry(cwd="/tmp")
    return Session(config=config, tool_registry=registry)


def _make_tool_response(text: str) -> ToolResponse:
    return ToolResponse(content=[TextBlock(text=text)], state=ToolResultState.SUCCESS, is_last=True)


class TestAgentLoop:
    """Test agent_loop behavior."""

    @pytest.mark.asyncio
    async def test_text_only_response(self) -> None:
        """Model responds with text, no tool calls, loop ends."""
        usage = ChatUsage(input_tokens=10, output_tokens=5, time=0.1)
        response = ChatResponse(
            content=[TextBlock(text="Hello")],
            is_last=True,
            usage=usage,
        )
        model = _StreamingFakeModel([[response]])
        client = ModelClient(model=model)
        session = _make_session()
        session.receive_user_message("Hi")

        events = []
        async for event in agent_loop(session, client):
            events.append(event)

        text_events = [e for e in events if isinstance(e, TextDelta)]
        assert any("Hello" in e.text for e in text_events)
        assert any(isinstance(e, TurnComplete) for e in events)

    @pytest.mark.asyncio
    async def test_tool_call_triggers_execution(self) -> None:
        """Model calls a tool, it executes, loop continues."""
        tool_call_response = ChatResponse(
            content=[
                ToolCallBlock(
                    id="call_1",
                    name="echo_tool",
                    input=json.dumps({"text": "ping"}),
                )
            ],
            is_last=True,
        )
        text_response = ChatResponse(
            content=[TextBlock(text="Got: pong")],
            is_last=True,
            usage=ChatUsage(input_tokens=20, output_tokens=10, time=0.2),
        )

        model = _StreamingFakeModel([[tool_call_response], [text_response]])
        client = ModelClient(model=model)

        session = _make_session()
        session.receive_user_message("Test")

        async def echo_tool(text: str) -> ToolResponse:
            """Echo text back.

            Args:
                text: Text to echo.
            """
            return _make_tool_response("pong")

        session.tool_registry.register(echo_tool)

        events = []
        async for event in agent_loop(session, client):
            events.append(event)

        tool_calls = [e for e in events if isinstance(e, ToolCall)]
        assert any(e.name == "echo_tool" for e in tool_calls)
        assert any(isinstance(e, TurnComplete) for e in events)

    @pytest.mark.asyncio
    async def test_max_turns_limit(self) -> None:
        """Loop stops after max_turns with error."""
        tool_call = ChatResponse(
            content=[
                ToolCallBlock(
                    id="call_1",
                    name="loop_tool",
                    input="{}",
                )
            ],
            is_last=True,
        )
        model = _StreamingFakeModel([[tool_call]] * 10)
        client = ModelClient(model=model)
        session = _make_session()
        session.receive_user_message("Test")

        async def loop_tool() -> ToolResponse:
            """A tool."""
            return _make_tool_response("ok")

        session.tool_registry.register(loop_tool)

        events = []
        async for event in agent_loop(session, client, max_turns=3):
            events.append(event)

        errors = [e for e in events if isinstance(e, Error)]
        assert any("Maximum turns" in e.message for e in errors)

    @pytest.mark.asyncio
    async def test_cancellation(self) -> None:
        """Cancellation stops the loop."""
        tool_call = ChatResponse(
            content=[
                ToolCallBlock(
                    id="call_1",
                    name="slow_tool",
                    input="{}",
                )
            ],
            is_last=True,
        )

        model = _StreamingFakeModel([[tool_call]])
        client = ModelClient(model=model)
        session = _make_session()
        session.receive_user_message("Test")

        async def slow_tool() -> ToolResponse:
            """A slow tool."""
            await asyncio.sleep(0.5)
            return _make_tool_response("done")

        session.tool_registry.register(slow_tool)

        async def cancel_soon():
            await asyncio.sleep(0.1)
            session.cancel_event.set()

        asyncio.create_task(cancel_soon())

        events = []
        async for event in agent_loop(session, client):
            events.append(event)
            if isinstance(event, Error) and "Cancelled" in event.message:
                break

        assert any(
            isinstance(e, Error) and "Cancelled" in e.message for e in events
        )

    @pytest.mark.asyncio
    async def test_pending_input_drained(self) -> None:
        """Pending inputs are drained between turns."""
        response = ChatResponse(
            content=[TextBlock(text="OK")],
            is_last=True,
            usage=ChatUsage(input_tokens=5, output_tokens=3, time=0.1),
        )
        model = _StreamingFakeModel([[response]])
        client = ModelClient(model=model)
        session = _make_session()
        session.receive_user_message("First")

        session.enqueue_pending_input("Follow-up question")

        events = []
        async for event in agent_loop(session, client):
            events.append(event)

        user_messages = [m for m in session.messages if m.role == "user"]
        assert len(user_messages) == 2
        assert user_messages[1].content == "Follow-up question"


class TestRetryLogic:
    """Test retry and backoff logic."""

    def test_is_retryable_timeout(self) -> None:
        assert _is_retryable(Exception("Connection timed out")) is True

    def test_is_retryable_rate_limit(self) -> None:
        assert _is_retryable(Exception("rate limit exceeded 429")) is True

    def test_is_retryable_500(self) -> None:
        assert _is_retryable(Exception("HTTP 500 Internal Server Error")) is True

    def test_is_retryable_503(self) -> None:
        assert _is_retryable(Exception("503 Service Unavailable")) is True

    def test_is_not_retryable_bad_request(self) -> None:
        assert _is_retryable(Exception("400 Bad Request")) is False

    def test_is_not_retryable_invalid_key(self) -> None:
        assert _is_retryable(Exception("invalid api key")) is False

    def test_is_not_retryable_model_not_found(self) -> None:
        assert _is_retryable(Exception("model not found")) is False


class TestTokenUsage:
    """Test token usage accumulation."""

    @pytest.mark.asyncio
    async def test_token_usage_accumulated(self) -> None:
        """Multiple turns accumulate token usage."""
        response = ChatResponse(
            content=[TextBlock(text="Hello")],
            is_last=True,
            usage=ChatUsage(input_tokens=100, output_tokens=50, time=0.1),
        )
        model = _StreamingFakeModel([[response]])
        client = ModelClient(model=model)
        session = _make_session()
        session.receive_user_message("Hi")

        events = []
        async for event in agent_loop(session, client):
            events.append(event)

        turn_completes = [e for e in events if isinstance(e, TurnComplete)]
        assert len(turn_completes) >= 1
        final = turn_completes[-1]
        assert final.usage.input_tokens >= 100
        assert final.usage.output_tokens >= 50
