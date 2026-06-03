"""Tests for message adapter."""

from agentscope.message import (
    TextBlock,
    ToolCallBlock,
    UserMsg,
    SystemMsg,
    AssistantMsg,
    Msg,
)
from agentscope.model._model_response import ChatResponse, ChatUsage

from hicoder.protocol.adapter import (
    to_agentscope_messages,
    from_chat_response,
    create_tool_result,
)
from hicoder.protocol.events import TextDelta, ToolCall, ToolCallDone, TurnComplete
from hicoder.protocol.models import AgentMessage


class TestToAgentScopeMessages:
    """Test AgentMessage → AgentScope Msg conversion."""

    def test_user_message(self) -> None:
        messages = [AgentMessage(role="user", content="fix the bug in app.py")]
        result = to_agentscope_messages(messages)
        assert len(result) == 1
        assert isinstance(result[0], Msg)
        assert result[0].role == "user"
        assert result[0].get_text_content() == "fix the bug in app.py"

    def test_system_message(self) -> None:
        messages = [AgentMessage(role="system", content="You are a coding agent.")]
        result = to_agentscope_messages(messages)
        assert len(result) == 1
        assert result[0].role == "system"
        assert result[0].get_text_content() == "You are a coding agent."

    def test_multi_turn_conversation(self) -> None:
        messages = [
            AgentMessage(role="system", content="You are helpful."),
            AgentMessage(role="user", content="Hello"),
            AgentMessage(role="assistant", content="Hi there!"),
            AgentMessage(role="user", content="How are you?"),
        ]
        result = to_agentscope_messages(messages)
        assert len(result) == 4
        assert result[0].role == "system"
        assert result[1].role == "user"
        assert result[2].role == "assistant"
        assert result[3].role == "user"

    def test_tool_result_message(self) -> None:
        messages = [
            AgentMessage(role="tool", content="file1\nfile2", tool_call_id="call_123")
        ]
        result = to_agentscope_messages(messages)
        assert len(result) == 1
        # Tool results are converted to user text messages
        assert result[0].role == "user"
        text = result[0].get_text_content()
        assert "call_123" in text
        assert "file1\nfile2" in text


class TestFromChatResponse:
    """Test ChatResponse → AgentEvent conversion."""

    def _make_response(self, usage: ChatUsage | None = None, **blocks):
        content = []
        if "text" in blocks:
            content.append(TextBlock(text=blocks["text"]))
        if "tool_calls" in blocks:
            for tc in blocks["tool_calls"]:
                content.append(
                    ToolCallBlock(
                        id=tc.get("id", ""),
                        name=tc.get("name", ""),
                        input=tc.get("input", ""),
                    )
                )
        return ChatResponse(content=content, is_last=True, usage=usage)

    def test_text_response(self) -> None:
        response = self._make_response(text="Hello world")
        events = from_chat_response(response)
        text_events = [e for e in events if isinstance(e, TextDelta)]
        assert len(text_events) == 1
        assert text_events[0].text == "Hello world"
        assert any(isinstance(e, TurnComplete) for e in events)

    def test_tool_call_response(self) -> None:
        response = self._make_response(
            tool_calls=[
                {"id": "call_1", "name": "shell", "input": '{"command": "ls"}'}
            ]
        )
        events = from_chat_response(response)
        tool_events = [e for e in events if isinstance(e, ToolCall)]
        tool_done_events = [e for e in events if isinstance(e, ToolCallDone)]
        assert len(tool_events) == 1
        assert tool_events[0].id == "call_1"
        assert tool_events[0].name == "shell"
        assert len(tool_done_events) == 1

    def test_token_usage_extracted(self) -> None:
        usage = ChatUsage(input_tokens=100, output_tokens=50, time=0.5)
        response = self._make_response(text="Hi", usage=usage)
        events = from_chat_response(response)
        turn_complete = next(
            (e for e in events if isinstance(e, TurnComplete)), None
        )
        assert turn_complete is not None
        assert turn_complete.usage.prompt_tokens == 100
        assert turn_complete.usage.completion_tokens == 50
        assert turn_complete.usage.total_tokens == 150


class TestCreateToolResult:

    def test_tool_result_created(self) -> None:
        result = create_tool_result("call_abc", "exit 0\nstdout: done")
        assert result.role == "tool"
        assert result.content == "exit 0\nstdout: done"
        assert result.tool_call_id == "call_abc"
