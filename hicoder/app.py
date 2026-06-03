"""HiCoder CLI: a Codex-style coding agent."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from hicoder.auth import resolve_api_key
from hicoder.config import Config, load_config
from hicoder.models.model_client import ModelClient
from hicoder.protocol import AgentEvent, AgentMessage, Error, TextDelta, ToolCall, TurnComplete

app = typer.Typer(
    name="hicoder",
    help="A Codex-style coding agent.",
    add_completion=False,
)
console = Console()


def load_agents_md(project_dir: Path | None) -> str | None:
    if not project_dir:
        return None
    agents_file = project_dir / "AGENTS.md"
    if agents_file.is_file():
        return agents_file.read_text()
    return None


def _load_client(config_path: Path) -> ModelClient:
    cfg = load_config(config_path)
    cfg.api_key = resolve_api_key(cfg.provider, cfg.api_key)
    return ModelClient.from_config(cfg)


async def _chat_loop(client: ModelClient, project_dir: Path | None) -> None:
    messages: list[AgentMessage] = []

    instructions = load_agents_md(project_dir)
    if instructions:
        messages.append(AgentMessage(role="system", content=instructions))

    console.print("HiCoder - Codex-style coding agent")
    console.print("Type [bold]exit[/] or [bold]quit[/] to leave, [bold]clear[/] to reset.")
    console.print()

    while True:
        try:
            user_input = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print()
            break

        if user_input in ("exit", "quit"):
            break

        if user_input == "clear":
            messages = messages[:1]
            console.print("Conversation cleared.")
            continue

        if not user_input:
            continue

        messages.append(AgentMessage(role="user", content=user_input))

        assistant_text = ""
        async for event in client.stream(messages=messages):
            if isinstance(event, TextDelta):
                console.print(event.text, end="")
                assistant_text += event.text
            elif isinstance(event, ToolCall):
                console.print(f"\n[Tool: {event.name}] {event.arguments}")
            elif isinstance(event, TurnComplete):
                console.print(
                    f"\n(Tokens: {event.usage.total_tokens} "
                    f"| in={event.usage.input_tokens} "
                    f"out={event.usage.output_tokens})"
                )
            elif isinstance(event, Error):
                console.print(f"\n[Error] {event.message}")

        if assistant_text:
            messages.append(AgentMessage(role="assistant", content=assistant_text))

        console.print()


@app.callback(invoke_without_command=True)
def chat(
    ctx: typer.Context,
    config: Path = typer.Option(..., "-c", "--config", help="Path to config.json"),
    project_dir: Optional[Path] = typer.Option(
        None,
        "-p",
        "--project-dir",
        help="Project directory to load AGENTS.md from",
    ),
) -> None:
    """Start an interactive chat session."""
    client = _load_client(config)
    asyncio.run(_chat_loop(client, project_dir))


if __name__ == "__main__":
    app()
