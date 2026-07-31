"""Tests for parsing and safely writing ```file:NAME fenced blocks.

The fence convention is the one the council stack already uses. Parsing has
to be robust to a real hazard: a submitted file can itself contain a ```
fence (a markdown README, a docs snippet). CommonMark's variable-length
fence rule handles that, so we follow it — an opening fence of N backticks
is closed only by a line of >= N backticks.
"""

from __future__ import annotations

import pytest

from harness.file_blocks import UnsafePathError, parse_file_blocks, write_file_blocks


def test_parses_single_block():
    text = "```file:app.py\nprint('hi')\n```"
    assert parse_file_blocks(text) == {"app.py": "print('hi')\n"}


def test_parses_multiple_blocks_with_prose_between():
    text = (
        "Here is the server.\n\n"
        "```file:server.py\nA\n```\n\n"
        "And the compose file.\n\n"
        "```file:docker-compose.yml\nB\n```\n"
    )
    assert parse_file_blocks(text) == {"server.py": "A\n", "docker-compose.yml": "B\n"}


def test_parses_nested_subdirectory_paths():
    text = "```file:src/poker/table.py\nX\n```"
    assert parse_file_blocks(text) == {"src/poker/table.py": "X\n"}


def test_longer_fence_allows_inner_triple_backticks():
    """A README that itself contains a ``` fence must survive intact."""
    text = "````file:README.md\n# Title\n\n```python\ncode\n```\n````"
    assert parse_file_blocks(text) == {"README.md": "# Title\n\n```python\ncode\n```\n"}


def test_unclosed_fence_is_ignored_not_half_written():
    """A truncated response (hit max_tokens mid-file) must not yield a
    partial file — writing half a source file would be scored as a model
    defect when it is really a transport truncation."""
    text = "```file:whole.py\ncomplete\n```\n```file:cut.py\nhalf written"
    assert parse_file_blocks(text) == {"whole.py": "complete\n"}


def test_empty_file_block_is_preserved():
    text = "```file:__init__.py\n```"
    assert parse_file_blocks(text) == {"__init__.py": ""}


def test_crlf_line_endings_are_normalised():
    text = "```file:a.py\r\nX\r\n```"
    assert parse_file_blocks(text) == {"a.py": "X\n"}


def test_no_blocks_returns_empty():
    assert parse_file_blocks("I refuse to answer.") == {}


def test_later_block_wins_on_duplicate_filename():
    text = "```file:a.py\nfirst\n```\n```file:a.py\nsecond\n```"
    assert parse_file_blocks(text) == {"a.py": "second\n"}


def test_language_hint_fence_is_not_a_file_block():
    """A plain ```python fence is prose, not a submission."""
    assert parse_file_blocks("```python\nx = 1\n```") == {}


def test_write_creates_nested_dirs(tmp_path):
    written = write_file_blocks(tmp_path, {"src/pkg/m.py": "X\n"})
    assert (tmp_path / "src/pkg/m.py").read_text() == "X\n"
    assert written == [tmp_path / "src/pkg/m.py"]


@pytest.mark.parametrize(
    "bad",
    ["../escape.py", "a/../../escape.py", "/etc/passwd", "~/x.py"],
)
def test_rejects_paths_escaping_the_impl_dir(tmp_path, bad):
    with pytest.raises(UnsafePathError):
        write_file_blocks(tmp_path, {bad: "pwned"})


def test_rejects_symlink_escape(tmp_path):
    """A model could emit a symlink-then-write pair across iterations; the
    resolved destination must still land inside impl_dir."""
    outside = tmp_path / "outside"
    outside.mkdir()
    impl = tmp_path / "impl"
    impl.mkdir()
    (impl / "link").symlink_to(outside, target_is_directory=True)
    with pytest.raises(UnsafePathError):
        write_file_blocks(impl, {"link/x.py": "pwned"})


def test_rejects_escape_before_writing_anything(tmp_path):
    """All-or-nothing: one bad path must not leave good files half-applied,
    otherwise a retry sees an inconsistent tree."""
    with pytest.raises(UnsafePathError):
        write_file_blocks(tmp_path, {"good.py": "A\n", "../bad.py": "B\n"})
    assert not (tmp_path / "good.py").exists()
