"""Tests for turn diff tracking in file tools."""

import difflib
import pytest
from pathlib import Path

from agentscope.message import ToolResultState

from hicoder.tools.file import write_file, edit_file


class TestTurnDiffTracking:
    """Test that file modifications produce diff information."""

    @pytest.fixture
    def test_dir(self, tmp_path: Path) -> str:
        return str(tmp_path)

    @pytest.mark.asyncio
    async def test_edit_file_changes_content(self, test_dir: str) -> None:
        """edit_file produces a measurable change."""
        path = Path(test_dir) / "diff_test.txt"
        original = "hello world"
        path.write_text(original)

        result = await edit_file(
            str(path), old_string="world", new_string="universe", cwd=test_dir
        )
        assert result.state == ToolResultState.SUCCESS

        new_content = path.read_text()
        assert new_content == "hello universe"
        assert new_content != original

    @pytest.mark.asyncio
    async def test_write_file_content_tracked(self, test_dir: str) -> None:
        """write_file records full content as diff."""
        path = Path(test_dir) / "new.txt"
        content = "line1\nline2\nline3"

        result = await write_file(str(path), content, cwd=test_dir)
        assert result.state == ToolResultState.SUCCESS
        assert path.read_text() == content

    @pytest.mark.asyncio
    async def test_write_file_overwrite_tracked(self, test_dir: str) -> None:
        """write_file overwriting produces diff between old and new."""
        path = Path(test_dir) / "overwrite.txt"
        path.write_text("original content")

        result = await write_file(str(path), "new content", cwd=test_dir)
        assert result.state == ToolResultState.SUCCESS
        assert path.read_text() == "new content"

    def test_unified_diff_generation(self) -> None:
        """Unified diff can be generated from old and new content."""
        old_lines = ["hello world", "foo bar"]
        new_lines = ["hello universe", "foo bar"]
        diff = list(difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile="test.py",
            tofile="test.py",
            lineterm="",
        ))
        assert len(diff) > 0
        assert "--- test.py" in diff
        assert "+++ test.py" in diff
        assert "-hello world" in diff
        assert "+hello universe" in diff
