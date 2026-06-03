"""Tests for model client."""

from dataclasses import dataclass
from typing import AsyncGenerator

import pytest

from agentscope.credential import OpenAICredential
from agentscope.message import TextBlock, ToolCallBlock
from agentscope.model import ChatModelBase, ChatResponse, ChatUsage
from agentscope.message import Msg

from hicoder.models.model_client import ModelClient, ModelParams
from hicoder.protocol.events import TextDelta, ToolCall, ToolCallDone, TurnComplete, Error
from hicoder.protocol.models import AgentMessage


class _FakeModel(ChatModelBase):
    """Fake model for testing that yields predefined ChatResponses."""

    class Parameters(ChatModelBase.Parameters):
        pass

    def __init__(self, responses: list[ChatResponse]) -> None:
        self._responses = responses
        # Need a credential for base class
        cred = OpenAICredential(api_key="fake-key")
        super().__init__(
            credential=cred,
            model="fake-model",
            parameters=self.Parameters(),
            stream=True,
        )

    async def _call_api(self, model_name, messages, tools=None, tool_choice=None, **kwargs):
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
        """Tool call response yields ToolCall + ToolCallDone + TurnComplete."""
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
        tool_done = [e for e in events if isinstance(e, ToolCallDone)]
        assert len(tool_calls) == 1
        assert tool_calls[0].name == "shell"
        assert tool_calls[0].arguments == '{"command": "ls"}'
        assert len(tool_done) == 1
        assert tool_done[0].id == "call_1"

    @pytest.mark.asyncio
    async def test_stream_error_yields_error_event(self) -> None:
        """When model raises exception, Error event is yielded."""
        model = _FakeModel([])
        # Override to raise an error
        async def bad_call(*args, **kwargs):
            raise ConnectionError("Network timeout")

        model._call_api = bad_call
        client = ModelClient(model=model)

        events = []
        async for event in client.stream(
            [AgentMessage(role="user", content="Hi")]
        ):
            events.append(event)

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
