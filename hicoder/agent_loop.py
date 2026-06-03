"""Agent loop: the core turn engine for HiCoder.

Drives a complete agent turn cycle: build context → call model → parse tool calls
→ execute tools → return results → repeat until no tool calls remain.
Yields AgentScope AgentEvent objects directly for UI consumption.

Supports:
- Retry with exponential backoff for transient errors
- Cancellation via asyncio.Event
- Pending input queue for mid-turn user interruption
- Token usage tracking across all turns
- Maximum turn limit (default: 50)
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import AsyncGenerator

from hicoder.models.model_client import ModelClient
from hicoder.protocol import (
    AgentEvent,
    AgentMessage,
    Error,
    TextDelta,
    TokenUsage,
    ToolCall,
    ToolCallDone,
    TurnComplete,
)
from hicoder.session import Session


# Retryable HTTP status codes (5xx and common transient)
_RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}

# Maximum retries for transient errors
MAX_RETRIES = 3

# Initial backoff delay in seconds
INITIAL_BACKOFF = 1.0

# Maximum backoff delay in seconds
MAX_BACKOFF = 30.0

# Default maximum turns per user message
DEFAULT_MAX_TURNS = 50


@dataclass
class UsageAccumulator:
    """Accumulated token usage across all turns."""

    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


def _is_retryable(error: Exception) -> bool:
    """Check if an error is transient and worth retrying."""
    msg = str(error).lower()
    if "timeout" in msg or "timed out" in msg:
        return True
    if "rate limit" in msg or "429" in msg:
        return True
    for code in _RETRYABLE_STATUS:
        if str(code) in msg:
            return True
    if any(x in msg for x in ["connection", "unreachable", "refused"]):
        return True
    return False


async def _call_model_with_retry(
    client: ModelClient,
    messages: list[AgentMessage],
    tools: list[dict] | None,
) -> AsyncGenerator[AgentEvent, None]:
    """Call the model with exponential backoff retry.

    Yields all events from the model response. On retryable error,
    yields Error events and retries with backoff.
    """
    for attempt in range(MAX_RETRIES + 1):
        if attempt > 0:
            delay = min(INITIAL_BACKOFF * (2 ** (attempt - 1)), MAX_BACKOFF)
            yield Error(message=f"Retry {attempt}/{MAX_RETRIES} in {delay:.0f}s...")
            await asyncio.sleep(delay)

        try:
            async for event in client.stream(messages=messages, tools=tools):
                yield event
            return  # Success

        except Exception as e:
            if not _is_retryable(e):
                yield Error(message=str(e))
                return
            # Continue to next retry attempt

    yield Error(message="Max retries exceeded")


async def agent_loop(
    session: Session,
    client: ModelClient,
    max_turns: int = DEFAULT_MAX_TURNS,
) -> AsyncGenerator[AgentEvent, None]:
    """Execute a complete agent turn cycle.

    Yields AgentEvent objects from AgentScope's event system, plus HiCoder
    Error and TurnComplete events.
    """
    usage = UsageAccumulator()
    turn_count = 0

    while turn_count < max_turns:
        # Check cancellation
        if session.cancel_event.is_set():
            yield Error(message="Cancelled")
            return

        # Drain pending inputs (mid-turn user interruption)
        new_inputs = session.drain_pending_inputs()
        session.messages.extend(new_inputs)

        # Build context: get tool definitions on first turn
        tool_defs = None
        if turn_count == 0:
            tool_defs = await session.tool_registry.get_tool_definitions()

        # Call model with retry
        events: list[AgentEvent] = []
        async for event in _call_model_with_retry(
            client=client,
            messages=session.messages,
            tools=tool_defs,
        ):
            events.append(event)
            yield event

        # Check if the last event was an error (from retry failure)
        if events and isinstance(events[-1], Error):
            return

        # Extract assistant text and tool calls from model response
        assistant_text_parts: list[str] = []
        tool_calls: list[tuple[str, dict, str]] = []  # (name, args, call_id)

        for event in events:
            if isinstance(event, TextDelta):
                assistant_text_parts.append(event.text)
            elif isinstance(event, ToolCall):
                try:
                    args = json.loads(event.arguments) if event.arguments else {}
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append((event.name, args, event.id))
            elif isinstance(event, TurnComplete):
                # Accumulate token usage from TurnComplete
                usage.input_tokens += event.usage.input_tokens
                usage.output_tokens += event.usage.output_tokens

        # Save assistant text to history
        assistant_text = "".join(assistant_text_parts)
        if assistant_text:
            session.append_assistant_message(assistant_text)

        turn_count += 1

        # If no tool calls, we're done
        if not tool_calls:
            yield TurnComplete(
                usage=TokenUsage(
                    prompt_tokens=usage.input_tokens,
                    completion_tokens=usage.output_tokens,
                    total_tokens=usage.total_tokens,
                )
            )
            return

        # Execute tool calls concurrently
        all_event_lists = await session.tool_registry.execute_batch(tool_calls)

        # Process tool execution results
        for i, (name, args, call_id) in enumerate(tool_calls):
            tool_events = all_event_lists[i] if i < len(all_event_lists) else []

            output_parts = []
            for ev in tool_events:
                if isinstance(ev, TextDelta):
                    output_parts.append(ev.text)
                yield ev

            output = "\n".join(output_parts)
            session.append_tool_result(call_id, output)

    # Max turns exceeded
    yield Error(message=f"Maximum turns ({max_turns}) reached")
