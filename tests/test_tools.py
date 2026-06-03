"""Tests for shell and file tools."""

import os
import pytest
from pathlib import Path

from agentscope.message import ToolResultState
from agentscope.tool._response import ToolResponse

from hicoder.tools.shell import shell
from hicoder.tools.file import read_file, write_file, edit_file
from hicoder.tools.truncation import truncate_text, TRUNCATION_NOTICE


class TestShellTool:
    """Test shell command execution."""

    @pytest.mark.asyncio
    async def test_echo_command(self) -> None:
        """Simple echo command succeeds."""
        result = await shell('echo "hello"')
        assert isinstance(result, ToolResponse)
        output = result.content[0].text
        assert "hello" in output

    @pytest.mark.asyncio
    async def test_stderr_capture(self) -> None:
        """Command with stderr captures it."""
        result = await shell("python3 -c \"import sys; sys.stderr.write('err'); sys.exit(0)\"")
        output = result.content[0].text
        assert "err" in output

    @pytest.mark.asyncio
    async def test_command_timeout(self) -> None:
        """Long-running command times out."""
        result = await shell("sleep 10", timeout=100)  # 100ms timeout
        assert result.state == ToolResultState.ERROR
        assert "timed out" in result.content[0].text.lower()

    @pytest.mark.asyncio
    async def test_command_in_cwd(self) -> None:
        """Command executes in specified working directory."""
        result = await shell("pwd", cwd="/tmp")
        output = result.content[0].text
        assert "/tmp" in output

    @pytest.mark.asyncio
    async def test_invalid_command(self) -> None:
        """Non-existent command fails."""
        result = await shell("nonexistent_command_xyz_123")
        assert result.state == ToolResultState.ERROR


class TestFileTools:
    """Test read_file, write_file, edit_file."""

    @pytest.fixture
    def test_dir(self, tmp_path: Path) -> str:
        return str(tmp_path)

    @pytest.mark.asyncio
    async def test_read_file(self, test_dir: str) -> None:
        """Read a file returns content with line numbers."""
        path = Path(test_dir) / "test.txt"
        path.write_text("line1\nline2\nline3")

        result = await read_file(str(path), cwd=test_dir)
        output = result.content[0].text
        assert "line1" in output
        assert "line2" in output

    @pytest.mark.asyncio
    async def test_read_file_not_found(self, test_dir: str) -> None:
        """Reading non-existent file returns error."""
        result = await read_file(str(Path(test_dir) / "nonexistent.txt"), cwd=test_dir)
        assert result.state == ToolResultState.ERROR
        assert "does not exist" in result.content[0].text

    @pytest.mark.asyncio
    async def test_read_file_relative_path_rejected(self, test_dir: str) -> None:
        """Relative path is rejected."""
        result = await read_file("relative/path.txt", cwd=test_dir)
        assert result.state == ToolResultState.ERROR

    @pytest.mark.asyncio
    async def test_write_file(self, test_dir: str) -> None:
        """Write file creates file with content."""
        path = Path(test_dir) / "new_file.txt"
        content = "Hello, World!"

        result = await write_file(str(path), content, cwd=test_dir)
        assert result.state == ToolResultState.SUCCESS
        assert path.read_text() == content

    @pytest.mark.asyncio
    async def test_write_file_creates_parents(self, test_dir: str) -> None:
        """Write file creates parent directories."""
        path = Path(test_dir) / "nested" / "dir" / "file.txt"

        result = await write_file(str(path), "content", cwd=test_dir)
        assert result.state == ToolResultState.SUCCESS
        assert path.read_text() == "content"

    @pytest.mark.asyncio
    async def test_write_file_outside_cwd_rejected(self, test_dir: str) -> None:
        """Path outside cwd is rejected."""
        result = await write_file("/tmp/outside_test.txt", "content", cwd=test_dir)
        assert result.state == ToolResultState.ERROR

    @pytest.mark.asyncio
    async def test_edit_file(self, test_dir: str) -> None:
        """Edit file replaces exact string."""
        path = Path(test_dir) / "edit_test.txt"
        path.write_text("hello world")

        result = await edit_file(
            str(path), old_string="world", new_string="universe", cwd=test_dir
        )
        assert result.state == ToolResultState.SUCCESS
        assert path.read_text() == "hello universe"

    @pytest.mark.asyncio
    async def test_edit_file_old_string_not_found(self, test_dir: str) -> None:
        """Edit with non-existent old_string returns error."""
        path = Path(test_dir) / "edit_test2.txt"
        path.write_text("hello world")

        result = await edit_file(
            str(path), old_string="missing", new_string="x", cwd=test_dir
        )
        assert result.state == ToolResultState.ERROR
        assert "not found" in result.content[0].text

    @pytest.mark.asyncio
    async def test_edit_file_ambiguous(self, test_dir: str) -> None:
        """Edit with ambiguous old_string returns error."""
        path = Path(test_dir) / "edit_test3.txt"
        path.write_text("hello hello")

        result = await edit_file(
            str(path), old_string="hello", new_string="x", cwd=test_dir
        )
        assert result.state == ToolResultState.ERROR
        assert "appears" in result.content[0].text

    @pytest.mark.asyncio
    async def test_edit_file_nonexistent(self, test_dir: str) -> None:
        """Editing non-existent file returns error."""
        result = await edit_file(
            str(Path(test_dir) / "nonexistent.txt"),
            old_string="x",
            new_string="y",
            cwd=test_dir,
        )
        assert result.state == ToolResultState.ERROR


class TestTruncation:
    """Test output truncation."""

    def test_small_text_not_truncated(self) -> None:
        text = "short text"
        result, truncated = truncate_text(text, max_bytes=100)
        assert result == text
        assert truncated is False

    def test_large_text_truncated(self) -> None:
        text = "x" * 1000
        result, truncated = truncate_text(text, max_bytes=100)
        assert truncated is True
        # Truncated bytes + notice should be close to max_bytes
        assert len(result.encode("utf-8")) <= 130

    def test_truncation_notice_appended(self) -> None:
        text = "x" * 1000
        result, truncated = truncate_text(text, max_bytes=100)
        assert TRUNCATION_NOTICE in result
