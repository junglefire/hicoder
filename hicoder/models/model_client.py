"""Model client: wraps AgentScope models with HiCoder event protocol.

Extends the model's stream() method to accept tool definitions and
yield AgentScope AgentEvent objects directly (TextBlockDelta, ToolCallStart,
etc.) plus HiCoder Error and TurnComplete events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import AsyncGenerator

from agentscope.credential import AnthropicCredential, OpenAICredential
from agentscope.message import TextBlock, ToolCallBlock
from agentscope.model import (
    AnthropicChatModel,
    ChatModelBase,
    ChatResponse,
    OpenAIChatModel,
)

from hicoder.config import Config
from hicoder.protocol import (
    AgentEvent,
    AgentMessage,
    Error,
    TextDelta,
    TokenUsage,
    ToolCall,
    ToolCallDone,
    TurnComplete,
    from_chat_response,
    to_agentscope_messages,
)


@dataclass
class ModelParams:
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    reasoning_effort: str | None = None


class ModelClient:
    def __init__(
        self,
        model: ChatModelBase,
        params: ModelParams | None = None,
    ) -> None:
        self._model = model
        self.params = params or ModelParams()

    @classmethod
    def from_config(cls, config: Config) -> "ModelClient":
        if config.api_key is None:
            raise ValueError(
                "api_key must be set before creating ModelClient. "
                "Call resolve_api_key() first."
            )

        if config.provider == "openai":
            credential = OpenAICredential(api_key=config.api_key, base_url=config.base_url)
            params = OpenAIChatModel.Parameters(
                max_tokens=config.max_tokens,
                temperature=None,
            )
            model = OpenAIChatModel(
                credential=credential,
                model=config.model,
                parameters=params,
                stream=True,
            )
        elif config.provider == "anthropic":
            credential = AnthropicCredential(api_key=config.api_key, base_url=config.base_url)
            params = AnthropicChatModel.Parameters(
                max_tokens=config.max_tokens,
                temperature=None,
            )
            model = AnthropicChatModel(
                credential=credential,
                model=config.model,
                parameters=params,
                stream=True,
            )
        else:
            raise ValueError(f"Unknown provider: {config.provider}")

        return cls(model=model)

    async def stream(
        self,
        messages: list[AgentMessage],
        tools: list[dict] | None = None,
    ) -> AsyncGenerator[AgentEvent, None]:
        """Stream model response events.

        When the model streams (streaming=True), yields incremental
        ChatResponse chunks. The final chunk (is_last=True) contains
        the complete response, which is converted to HiCoder events
        via from_chat_response().

        When tools are provided, they are passed to AgentScope's model
        as JSON Schema definitions for function calling.

        Args:
            messages: Conversation history as AgentMessage list.
            tools: Optional list of OpenAI-compatible tool definitions.

        Yields:
            AgentEvent objects: TextDelta for text, ToolCall/ToolCallDone
            for tool calls, TurnComplete for the final response, Error on failure.
        """
        try:
            as_messages = to_agentscope_messages(messages)

            # AgentScope models accept tools as list[dict] JSON Schema definitions
            response = await self._model(as_messages, tools=tools)

            if isinstance(response, ChatResponse):
                # Non-streaming: single response
                for event in from_chat_response(response):
                    yield event
            else:
                # Streaming: async generator of ChatResponse chunks
                accumulated_text: list[str] = []
                final_response: ChatResponse | None = None

                async for chunk in response:
                    # Yield text deltas for incremental text
                    for block in chunk.content:
                        if isinstance(block, TextBlock) and block.text:
                            accumulated_text.append(block.text)
                            yield TextDelta(text=block.text)
                        elif isinstance(block, ToolCallBlock):
                            yield ToolCall(
                                id=block.id or "",
                                name=block.name or "",
                                arguments=block.input or "",
                            )

                    if chunk.is_last:
                        final_response = chunk

                # Yield TurnComplete with usage from the final chunk
                if final_response is not None:
                    usage = TokenUsage(
                        prompt_tokens=final_response.usage.input_tokens if final_response.usage else 0,
                        completion_tokens=final_response.usage.output_tokens if final_response.usage else 0,
                        total_tokens=(
                            (final_response.usage.input_tokens + final_response.usage.output_tokens)
                            if final_response.usage
                            else 0
                        ),
                    )
                    yield TurnComplete(usage=usage)

        except Exception as e:
            yield Error(message=str(e))
            raise
