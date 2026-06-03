"""File operation tools: read_file, write_file, edit_file.

Uses AgentScope's ToolResponse and TextBlock for consistent output format.
All tools require absolute paths and enforce a working directory constraint.
"""

from __future__ import annotations

import os
from pathlib import Path

from agentscope.message import TextBlock, ToolResultState
from agentscope.tool._response import ToolResponse

MAX_OUTPUT_BYTES = 20000


def _validate_path(file_path: str, cwd: str) -> Path | None:
    """Validate that file_path is absolute and within cwd."""
    if not os.path.isabs(file_path):
        return None

    resolved = Path(file_path).resolve()
    work_dir = Path(cwd).resolve()

    try:
        resolved.relative_to(work_dir)
    except ValueError:
        return None

    return resolved


async def read_file(
    file_path: str,
    cwd: str = "",
    offset: int = 1,
    limit: int | None = None,
) -> ToolResponse:
    """Read a file and return its content with line numbers."""
    work_dir = cwd or os.getcwd()
    path = _validate_path(file_path, work_dir)
    if path is None:
        return ToolResponse(
            content=[TextBlock(text=f"Error: invalid path '{file_path}'. Must be absolute and within {work_dir}")],
            state=ToolResultState.ERROR,
            is_last=True,
        )

    if not path.is_file():
        return ToolResponse(
            content=[TextBlock(text=f"Error: File does not exist or is not a file: {file_path}")],
            state=ToolResultState.ERROR,
            is_last=True,
        )

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()

        start = offset - 1
        if limit:
            selected = lines[start : start + limit]
        else:
            selected = lines[start:]

        total_bytes = 0
        output_lines = []
        for line in selected:
            if total_bytes + len(line) > MAX_OUTPUT_BYTES:
                output_lines.append("... (output truncated)")
                break
            output_lines.append(line)
            total_bytes += len(line) + 1

        result_lines = []
        for i, line in enumerate(output_lines, start=offset):
            result_lines.append(f"{i:6d}\t{line}")

        return ToolResponse(
            content=[TextBlock(text="\n".join(result_lines))],
            state=ToolResultState.SUCCESS,
            is_last=True,
        )
    except Exception as e:
        return ToolResponse(
            content=[TextBlock(text=f"Error reading file: {e}")],
            state=ToolResultState.ERROR,
            is_last=True,
        )


async def write_file(
    file_path: str,
    content: str,
    cwd: str = "",
) -> ToolResponse:
    """Write content to a file, creating parent directories if needed."""
    work_dir = cwd or os.getcwd()
    path = _validate_path(file_path, work_dir)
    if path is None:
        return ToolResponse(
            content=[TextBlock(text=f"Error: invalid path '{file_path}'. Must be absolute and within {work_dir}")],
            state=ToolResultState.ERROR,
            is_last=True,
        )

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return ToolResponse(
            content=[TextBlock(text=f"Successfully wrote {len(content)} bytes to {file_path}")],
            state=ToolResultState.SUCCESS,
            is_last=True,
        )
    except Exception as e:
        return ToolResponse(
            content=[TextBlock(text=f"Error writing file: {e}")],
            state=ToolResultState.ERROR,
            is_last=True,
        )


async def edit_file(
    file_path: str,
    old_string: str,
    new_string: str,
    cwd: str = "",
) -> ToolResponse:
    """Perform exact string replacement in a file."""
    work_dir = cwd or os.getcwd()
    path = _validate_path(file_path, work_dir)
    if path is None:
        return ToolResponse(
            content=[TextBlock(text=f"Error: invalid path '{file_path}'. Must be absolute and within {work_dir}")],
            state=ToolResultState.ERROR,
            is_last=True,
        )

    if not path.is_file():
        return ToolResponse(
            content=[TextBlock(text=f"Error: File does not exist: {file_path}")],
            state=ToolResultState.ERROR,
            is_last=True,
        )

    try:
        content = path.read_text(encoding="utf-8")
        count = content.count(old_string)

        if count == 0:
            return ToolResponse(
                content=[TextBlock(text=f"Error: old_string not found in {file_path}")],
                state=ToolResultState.ERROR,
                is_last=True,
            )
        if count > 1:
            return ToolResponse(
                content=[TextBlock(text=f"Error: old_string appears {count} times in {file_path}, must be unique")],
                state=ToolResultState.ERROR,
                is_last=True,
            )

        new_content = content.replace(old_string, new_string, 1)
        path.write_text(new_content, encoding="utf-8")
        return ToolResponse(
            content=[TextBlock(text=f"Successfully edited {file_path}")],
            state=ToolResultState.SUCCESS,
            is_last=True,
        )
    except Exception as e:
        return ToolResponse(
            content=[TextBlock(text=f"Error editing file: {e}")],
            state=ToolResultState.ERROR,
            is_last=True,
        )
