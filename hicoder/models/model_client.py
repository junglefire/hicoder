"""Model client: wraps AgentScope models with HiCoder event protocol."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import AsyncGenerator, Literal

from agentscope.credential import AnthropicCredential, OpenAICredential
from agentscope.message import Msg
from agentscope.model import (
    AnthropicChatModel,
    ChatModelBase,
    ChatResponse,
    OpenAIChatModel,
)

from ..config import Config
from ..protocol.adapter import from_chat_response, to_agentscope_messages
from ..protocol.events import AgentEvent, Error
from ..protocol.models import AgentMessage


@dataclass
class ModelParams:
    """Parameters passed to the model on each call."""

    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    reasoning_effort: str | None = None


class ModelClient:
    """Wraps an AgentScope model and yields HiCoder AgentEvent objects.

    Usage::

        client = ModelClient.from_config(config)
        async for event in client.stream(
            messages=[AgentMessage(role="user", content="Hello")]
        ):
            if isinstance(event, TextDelta):
                print(event.text, end="")
            elif isinstance(event, TurnComplete):
                print(f"\\nTokens: {event.usage.total_tokens}")
    """

    def __init__(
        self,
        model: ChatModelBase,
        params: ModelParams | None = None,
    ) -> None:
        self._model = model
        self.params = params or ModelParams()

    @classmethod
    def from_config(cls, config: Config) -> "ModelClient":
        """Create a ModelClient from a loaded HiCoder Config.

        Args:
            config: The loaded configuration with api_key resolved.

        Returns:
            A ready-to-use ModelClient.

        Raises:
            ValueError: If the provider is unknown.
        """
        if config.api_key is None:
            raise ValueError(
                "api_key must be set before creating ModelClient. "
                "Call resolve_api_key() first."
            )

        if config.provider == "openai":
            credential = OpenAICredential(api_key=config.api_key)
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
            credential = AnthropicCredential(api_key=config.api_key)
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
        """Stream model response as HiCoder AgentEvent objects.

        Args:
            messages: List of conversation messages.
            tools: Optional tool definitions (JSON Schema format).

        Yields:
            AgentEvent objects: TextDelta, ToolCall, ToolCallDone, TurnComplete, Error.
        """
        try:
            as_messages = to_agentscope_messages(messages)
            response = await self._model(as_messages, tools=tools)

            if isinstance(response, ChatResponse):
                # Non-streaming: single response
                for event in from_chat_response(response):
                    yield event
            else:
                # Streaming: async generator
                final_response: ChatResponse | None = None
                async for chunk in response:
                    # Only yield the final complete response as events
                    # to avoid emitting partial content multiple times
                    if chunk.is_last:
                        final_response = chunk

                if final_response is not None:
                    for event in from_chat_response(final_response):
                        yield event

        except Exception as e:
            yield Error(message=str(e))
