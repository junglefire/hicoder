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

from hicoder.config import Config
from hicoder.protocol import (
    AgentEvent,
    AgentMessage,
    Error,
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
        try:
            as_messages = to_agentscope_messages(messages)
            response = await self._model(as_messages, tools=tools)

            if isinstance(response, ChatResponse):
                for event in from_chat_response(response):
                    yield event
            else:
                final_response: ChatResponse | None = None
                async for chunk in response:
                    if chunk.is_last:
                        final_response = chunk

                if final_response is not None:
                    for event in from_chat_response(final_response):
                        yield event

        except Exception as e:
            yield Error(message=str(e))
