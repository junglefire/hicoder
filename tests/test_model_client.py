"""Tests for model client."""

import pytest

from agentscope.credential import OpenAICredential
from agentscope.message import TextBlock, ToolCallBlock
from agentscope.model import ChatModelBase, ChatResponse, ChatUsage

from hicoder.models.model_client import ModelClient, ModelParams
from hicoder.protocol.events import TextDelta, ToolCall, ToolCallDone, TurnComplete, Error
from hicoder.protocol.models import AgentMessage


class _FakeModel(ChatModelBase):
    """Fake model for testing that yields predefined ChatResponses."""

    class Parameters(ChatModelBase.Parameters):
        pass

    def __init__(
        self,
        responses: list[ChatResponse],
        should_raise: Exception | None = None,
        max_retries: int = 0,
    ) -> None:
        self._responses = responses
        self._should_raise = should_raise
        cred = OpenAICredential(api_key="fake-key")
        super().__init__(
            credential=cred,
            model="fake-model",
            parameters=self.Parameters(),
            stream=True,
            max_retries=max_retries,
        )

    async def _call_api(self, model_name, messages, tools=None, tool_choice=None, **kwargs):
        if self._should_raise:
            raise self._should_raise

        if self.stream:
            async def gen():
                for resp in self._responses:
                    yield resp
            return gen()
        return self._responses[0]


class TestModelClient:
    """Test ModelClient stream interface."""

    @pytest.mark.asyncio
    async def test_stream_text_response(self) -> None:
        """Text response yields TextDelta + TurnComplete."""
        usage = ChatUsage(input_tokens=10, output_tokens=5, time=0.1)
        response = ChatResponse(
            content=[TextBlock(text="Hello world")],
            is_last=True,
            usage=usage,
        )
        model = _FakeModel([response])
        client = ModelClient(model=model)

        events = []
        async for event in client.stream(
            [AgentMessage(role="user", content="Hi")]
        ):
            events.append(event)

        text_events = [e for e in events if isinstance(e, TextDelta)]
        assert len(text_events) == 1
        assert text_events[0].text == "Hello world"

        turn_complete = [e for e in events if isinstance(e, TurnComplete)]
        assert len(turn_complete) == 1
        assert turn_complete[0].usage.prompt_tokens == 10
        assert turn_complete[0].usage.completion_tokens == 5

    @pytest.mark.asyncio
    async def test_stream_tool_call_response(self) -> None:
        """Tool call response yields ToolCall + TurnComplete."""
        response = ChatResponse(
            content=[
                ToolCallBlock(
                    id="call_1",
                    name="shell",
                    input='{"command": "ls"}',
                )
            ],
            is_last=True,
        )
        model = _FakeModel([response])
        client = ModelClient(model=model)

        events = []
        async for event in client.stream(
            [AgentMessage(role="user", content="List files")]
        ):
            events.append(event)

        tool_calls = [e for e in events if isinstance(e, ToolCall)]
        assert len(tool_calls) == 1
        assert tool_calls[0].name == "shell"
        assert tool_calls[0].arguments == '{"command": "ls"}'
        # TurnComplete is yielded at the end
        assert any(isinstance(e, TurnComplete) for e in events)

    @pytest.mark.asyncio
    async def test_stream_error_yields_error_event(self) -> None:
        """When model raises exception, Error event is yielded and exception propagated."""
        model = _FakeModel(
            [],
            should_raise=ConnectionError("Network timeout"),
            max_retries=0,
        )
        client = ModelClient(model=model)

        events = []
        with pytest.raises(ConnectionError, match="Network timeout"):
            async for event in client.stream(
                [AgentMessage(role="user", content="Hi")]
            ):
                events.append(event)

        # Error event was yielded before the exception propagated
        errors = [e for e in events if isinstance(e, Error)]
        assert len(errors) == 1
        assert "Network timeout" in errors[0].message


class TestModelParams:
    """Test ModelParams dataclass."""

    def test_defaults(self) -> None:
        params = ModelParams()
        assert params.temperature is None
        assert params.max_tokens is None
        assert params.top_p is None
        assert params.reasoning_effort is None

    def test_custom_values(self) -> None:
        params = ModelParams(
            temperature=0.7,
            max_tokens=2048,
            top_p=0.9,
            reasoning_effort="medium",
        )
        assert params.temperature == 0.7
        assert params.max_tokens == 2048
        assert params.top_p == 0.9
        assert params.reasoning_effort == "medium"
