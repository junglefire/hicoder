"""Shell command execution tool for HiCoder.

Uses asyncio.create_subprocess_exec for command execution with
timeout control and output truncation. Commands execute within
the session's configured working directory (cwd).
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from agentscope.message import TextBlock, ToolResultState
from agentscope.tool._response import ToolResponse

DEFAULT_TIMEOUT_MS = 30000  # 30 seconds
MAX_OUTPUT_CHARS = 30000


async def shell(
    command: str,
    cwd: str = "",
    timeout: int = DEFAULT_TIMEOUT_MS,
) -> ToolResponse:
    """Execute a shell command and return stdout, stderr, and exit code.

    Args:
        command: The shell command to execute.
        cwd: Working directory for the command.
        timeout: Timeout in milliseconds (default: 30000).

    Returns:
        ToolResponse with combined stdout/stderr and exit status.
    """
    timeout_ms = min(timeout, 600000)
    timeout_sec = timeout_ms / 1000.0

    work_dir = cwd if cwd else os.getcwd()
    work_path = Path(work_dir)

    if not work_path.is_dir():
        return ToolResponse(
            content=[TextBlock(text=f"Working directory does not exist: {work_dir}")],
            state=ToolResultState.ERROR,
            is_last=True,
        )

    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(work_path),
        )

        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout_sec,
        )

        stdout = stdout_bytes.decode("utf-8", errors="replace").replace("\r\n", "\n")
        stderr = stderr_bytes.decode("utf-8", errors="replace").replace("\r\n", "\n")

        output = stdout
        if stderr:
            if output:
                output += "\n"
            output += stderr

        if len(output) > MAX_OUTPUT_CHARS:
            output = output[:MAX_OUTPUT_CHARS] + "\n... (output truncated)"

        if process.returncode != 0:
            result = f"Command failed (exit code {process.returncode}): {command}\n"
            if stdout:
                result += f"\nStdout:\n{stdout}"
            if stderr:
                result += f"\nStderr:\n{stderr}"
            if len(result) > MAX_OUTPUT_CHARS:
                result = result[:MAX_OUTPUT_CHARS] + "\n... (output truncated)"

            return ToolResponse(
                content=[TextBlock(text=result)],
                state=ToolResultState.ERROR,
                is_last=True,
            )

        return ToolResponse(
            content=[TextBlock(text=output)],
            state=ToolResultState.SUCCESS,
            is_last=True,
        )

    except asyncio.TimeoutError:
        return ToolResponse(
            content=[TextBlock(text=f"Command timed out after {timeout_ms}ms: {command}")],
            state=ToolResultState.ERROR,
            is_last=True,
        )
    except Exception as e:
        return ToolResponse(
            content=[TextBlock(text=f"Command failed: {command}\nError: {e}")],
            state=ToolResultState.ERROR,
            is_last=True,
        )
