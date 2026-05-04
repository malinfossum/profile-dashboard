from datetime import UTC, datetime

from src import renderer


def _repo(**overrides):
    base = {
        "name": "todo-list",
        "html_url": "https://github.com/malinfossum/todo-list",
        "description": "Vanilla JS MVC todo app",
        "language": "JavaScript",
        "pushed_at": "2026-04-30T12:34:56Z",
    }
    base.update(overrides)
    return base


class TestEscapeCell:
    def test_plain_text_unchanged(self):
        assert renderer._escape_cell("hello world") == "hello world"

    def test_pipe_escaped(self):
        assert renderer._escape_cell("a | b") == "a \\| b"

    def test_backtick_escaped(self):
        assert renderer._escape_cell("use `code`") == "use \\`code\\`"

    def test_brackets_escaped(self):
        assert renderer._escape_cell("[link]") == "\\[link\\]"

    def test_backslash_escaped_first(self):
        assert renderer._escape_cell("a\\b") == "a\\\\b"

    def test_none_renders_em_dash(self):
        assert renderer._escape_cell(None) == renderer.EMPTY_FIELD

    def test_empty_renders_em_dash(self):
        assert renderer._escape_cell("") == renderer.EMPTY_FIELD


class TestRenderFeaturedTable:
    def test_empty_list_shows_placeholder(self):
        out = renderer.render_featured_table([])
        assert "_No featured repos yet_" in out
        assert "| Project | About | Lang | Updated |" in out

    def test_single_repo_row(self):
        out = renderer.render_featured_table([_repo()])
        assert "[todo-list](https://github.com/malinfossum/todo-list)" in out
        assert "Vanilla JS MVC todo app" in out
        assert "JavaScript" in out
        assert "2026-04-30" in out

    def test_caps_at_featured_limit(self):
        repos = [_repo(name=f"repo-{i}") for i in range(10)]
        out = renderer.render_featured_table(repos)
        assert out.count("\n|") == 1 + renderer.FEATURED_LIMIT  # header sep + N rows

    def test_pipe_in_description_does_not_break_table(self):
        repo = _repo(description="before | after")
        out = renderer.render_featured_table([repo])
        # Real pipes inside cells are escaped, so the row still has 4 cell separators (5 pipes).
        row_line = [line for line in out.splitlines() if "before" in line][0]
        assert row_line.count("|") - row_line.count("\\|") == 5

    def test_null_description_renders_em_dash(self):
        repo = _repo(description=None)
        out = renderer.render_featured_table([repo])
        assert renderer.EMPTY_FIELD in out


class TestRenderStatsLine:
    def test_basic_line(self):
        when = datetime(2026, 5, 4, tzinfo=UTC)
        out = renderer.render_stats_line(24, ["JavaScript", "HTML", "CSS"], when)
        assert "24 public repos" in out
        assert "JavaScript, HTML, CSS" in out
        assert "Last updated 2026-05-04 (UTC)" in out

    def test_empty_languages_renders_em_dash(self):
        when = datetime(2026, 5, 4, tzinfo=UTC)
        out = renderer.render_stats_line(0, [], when)
        assert renderer.EMPTY_FIELD in out


class TestCompose:
    def test_includes_table_and_stats_only(self):
        when = datetime(2026, 5, 4, tzinfo=UTC)
        out = renderer.compose([_repo()], repo_count=1, languages=["JavaScript"], generated_at=when)
        assert "[todo-list]" in out
        assert "**Stats:**" in out
        assert "2026-05-04 (UTC)" in out

    def test_does_not_include_section_heading(self):
        # The block is data only; the target README owns its own headings.
        when = datetime(2026, 5, 4, tzinfo=UTC)
        out = renderer.compose([_repo()], repo_count=1, languages=["JavaScript"], generated_at=when)
        assert "###" not in out
        assert "What I'm building" not in out


class TestWrapWithMarkers:
    def test_wraps_block(self):
        out = renderer.wrap_with_markers("body")
        assert out.startswith(renderer.MARKER_START)
        assert out.endswith(renderer.MARKER_END)
        assert "body" in out
