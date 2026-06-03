"""Message adapter between HiCoder AgentMessage and AgentScope Msg."""

from __future__ import annotations

from agentscope.message import (
    Msg,
    TextBlock,
    ToolCallBlock,
    UserMsg,
    AssistantMsg,
    SystemMsg,
)
from agentscope.model._model_response import ChatResponse

from ..protocol.events import (
    AgentEvent,
    TextDelta,
    ToolCall,
    ToolCallDone,
    TurnComplete,
    Error,
    TokenUsage,
)
from ..protocol.models import AgentMessage


def to_agentscope_messages(messages: list[AgentMessage]) -> list[Msg]:
    """Convert HiCoder AgentMessage list to AgentScope Msg list.

    Args:
        messages: List of AgentMessage to convert.

    Returns:
        List of AgentScope Msg objects ready for model input.
    """
    result: list[Msg] = []
    for msg in messages:
        if msg.role == "system":
            result.append(SystemMsg(name="system", content=msg.content))
        elif msg.role == "user":
            result.append(UserMsg(name="user", content=msg.content))
        elif msg.role == "assistant":
            result.append(AssistantMsg(name="assistant", content=msg.content))
        elif msg.role == "tool" and msg.tool_call_id:
            # Tool results are sent as user text messages.
            # AgentScope's Msg(role="user") only accepts text/data blocks.
            result.append(
                UserMsg(
                    name="tool",
                    content=f"Tool call {msg.tool_call_id} output:\n{msg.content}",
                )
            )
    return result


def from_chat_response(response: ChatResponse) -> list[AgentEvent]:
    """Convert an AgentScope ChatResponse to HiCoder AgentEvent list.

    TextBlock content → TextDelta events.
    ToolCallBlock content → ToolCall + ToolCallDone events.

    Args:
        response: The ChatResponse from AgentScope model.

    Returns:
        List of AgentEvent objects.
    """
    events: list[AgentEvent] = []

    for block in response.content:
        if isinstance(block, TextBlock):
            if block.text:
                events.append(TextDelta(text=block.text))

        elif isinstance(block, ToolCallBlock):
            events.append(
                ToolCall(
                    id=block.id or "",
                    name=block.name or "",
                    arguments=block.input or "",
                )
            )
            events.append(
                ToolCallDone(
                    id=block.id or "",
                    name=block.name or "",
                    arguments=block.input or "",
                )
            )

    usage = TokenUsage(
        prompt_tokens=response.usage.input_tokens if response.usage else 0,
        completion_tokens=response.usage.output_tokens if response.usage else 0,
        total_tokens=(
            (response.usage.input_tokens + response.usage.output_tokens)
            if response.usage
            else 0
        ),
    )
    events.append(TurnComplete(usage=usage))

    return events


def create_tool_result(tool_call_id: str, output_text: str) -> AgentMessage:
    """Create a tool result AgentMessage for inclusion in the next model call.

    Args:
        tool_call_id: The ID of the tool call this result belongs to.
        output_text: The text output from the tool execution.

    Returns:
        An AgentMessage with role="tool".
    """
    return AgentMessage(
        role="tool",
        content=output_text,
        tool_call_id=tool_call_id,
    )
