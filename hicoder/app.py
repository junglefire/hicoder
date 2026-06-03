"""HiCoder CLI: a Codex-style coding agent."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from hicoder.agent_loop import agent_loop
from hicoder.auth import resolve_api_key
from hicoder.config import Config, load_config
from hicoder.models.model_client import ModelClient
from hicoder.protocol import AgentEvent, AgentMessage, Error, TextDelta, ToolCall, ToolCallDone, TurnComplete
from hicoder.session import Session
from hicoder.tools import ToolRegistry, read_file, write_file, edit_file, shell

app = typer.Typer(
    name="hicoder",
    help="A Codex-style coding agent.",
    add_completion=False,
)
console = Console()


def load_agents_md(project_dir: Path | None) -> str | None:
    """Load AGENTS.md from project directory if it exists."""
    if not project_dir:
        return None
    agents_file = project_dir / "AGENTS.md"
    if agents_file.is_file():
        return agents_file.read_text()
    return None


def _load_client(config_path: Path) -> ModelClient:
    """Load config and create ModelClient."""
    cfg = load_config(config_path)
    cfg.api_key = resolve_api_key(cfg.provider, cfg.api_key)
    return ModelClient.from_config(cfg)


def _register_tools(registry: ToolRegistry, cwd: str) -> None:
    """Register built-in tools with the registry.

    Each tool function is wrapped in AgentScope's FunctionTool and
    added to the registry's Toolkit for automatic schema generation.
    """
    # File tools (read-only)
    registry.register(read_file, is_read_only=True)
    registry.register(write_file)
    registry.register(edit_file)

    # Shell tool
    registry.register(shell)


async def _chat_loop(client: ModelClient, config: Config, project_dir: Path | None) -> None:
    """Interactive chat loop using the full agent_loop engine.

    Creates a Session with tool registry, registers built-in tools,
    and drives the agent_loop for each user message.
    """
    # Set up working directory
    if config.cwd and config.cwd != ".":
        work_dir = config.cwd
    elif project_dir:
        work_dir = str(project_dir.resolve())
    else:
        work_dir = os.getcwd()

    # Create session and register tools
    registry = ToolRegistry(cwd=work_dir)
    _register_tools(registry, work_dir)

    session = Session(config=config, tool_registry=registry)

    # Load AGENTS.md as system message
    instructions = load_agents_md(project_dir)
    if instructions:
        session.messages.append(AgentMessage(role="system", content=instructions))

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
            # Reset to system messages only
            if session.messages and session.messages[0].role == "system":
                session.messages = session.messages[:1]
            else:
                session.messages = []
            console.print("Conversation cleared.")
            continue

        if not user_input:
            continue

        # Add user message and run agent loop
        session.receive_user_message(user_input)

        assistant_text = ""
        tool_call_count = 0

        async for event in agent_loop(session=session, client=client):
            if isinstance(event, TextDelta):
                console.print(event.text, end="")
                assistant_text += event.text
            elif isinstance(event, ToolCall):
                tool_call_count += 1
                console.print(f"\n[Tool: {event.name}]")
            elif isinstance(event, ToolCallDone):
                pass  # ToolCallDone is implicit after ToolCall text output
            elif isinstance(event, TurnComplete):
                console.print(
                    f"\n(Tokens: {event.usage.total_tokens} "
                    f"| in={event.usage.input_tokens} "
                    f"out={event.usage.output_tokens})"
                )
            elif isinstance(event, Error):
                console.print(f"\n[Error] {event.message}")

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
    cfg = load_config(config)
    cfg.api_key = resolve_api_key(cfg.provider, cfg.api_key)
    asyncio.run(_chat_loop(client, cfg, project_dir))


if __name__ == "__main__":
    app()
