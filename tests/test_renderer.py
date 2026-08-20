"""Renderer tests pin the exact HTML the frozen README v6 design expects."""

from __future__ import annotations

from datetime import UTC, datetime

from src import renderer

TIDSRO = {
    "name": "tidsro",
    "html_url": "https://github.com/malinfossum/tidsro",
    "stargazers_count": 1,
    "description": "A calm desktop timer & alarm. Local-first, for Windows.",
}
IGNITE = {
    "name": "ignite",
    "html_url": "https://github.com/malinfossum/ignite",
    "stargazers_count": 1,
    "description": "ADHD-friendly task app. A small flame, kept going.",
}
VARDE = {
    "name": "varde",
    "html_url": "https://github.com/malinfossum/varde",
    "stargazers_count": 0,
    "description": "A bilingual directory of Norwegian social services.",
}
WINUTIL = {
    "full_name": "ChrisTitusTech/winutil",
    "html_url": "https://github.com/ChrisTitusTech/winutil",
    "stargazers_count": 60883,
    "prs": [
        {"number": 4995, "html_url": "https://github.com/ChrisTitusTech/winutil/pull/4995"},
        {"number": 4992, "html_url": "https://github.com/ChrisTitusTech/winutil/pull/4992"},
        {"number": 4993, "html_url": "https://github.com/ChrisTitusTech/winutil/pull/4993"},
    ],
}


class TestShortDescription:
    def test_first_sentence_lowercased(self):
        assert (
            renderer.short_description("A calm desktop timer & alarm. Local-first.")
            == "a calm desktop timer & alarm."
        )

    def test_acronym_opener_keeps_casing(self):
        assert (
            renderer.short_description("ADHD-friendly task app. A small flame.")
            == "ADHD-friendly task app."
        )

    def test_single_sentence_gains_period(self):
        assert renderer.short_description("Job radar for Norway") == "job radar for Norway."

    def test_empty_and_none(self):
        assert renderer.short_description(None) == ""
        assert renderer.short_description("") == ""


class TestFormatStars:
    def test_below_thousand_verbatim(self):
        assert renderer.format_stars(999) == "999"

    def test_thousands_one_decimal(self):
        assert renderer.format_stars(60883) == "60.9k"

    def test_trailing_zero_stripped(self):
        assert renderer.format_stars(60000) == "60k"


class TestGroupRow:
    def test_exact_row_html(self):
        row = renderer.render_group_row("focus", [TIDSRO, IGNITE])
        expected = (
            "<tr>\n"
            '<td valign="middle" width="30%">\n\n'
            '<img src="assets/chip-gold.svg" width="14" height="14" alt="" /> '
            "<strong>For focus</strong>\n\n"
            "<em>Calm tools, built for brains like mine.</em>\n\n"
            "</td>\n"
            '<td valign="top" width="70%">\n\n'
            '<a href="https://github.com/malinfossum/tidsro"><strong>tidsro</strong></a>'
            " ★ 1: a calm desktop timer &amp; alarm.\n\n"
            '<a href="https://github.com/malinfossum/ignite"><strong>ignite</strong></a>'
            " ★ 1: ADHD-friendly task app.\n\n"
            "</td>\n"
            "</tr>"
        )
        assert row == expected

    def test_zero_stars_omits_star_part(self):
        row = renderer.render_group_row("wellbeing", [VARDE])
        assert "varde</strong></a>: a bilingual" in row
        assert "★ 0" not in row


class TestContribRow:
    def test_pill_and_ascending_pr_links(self):
        row = renderer.render_contrib_row([WINUTIL], 3)
        assert (
            '<img src="assets/oss-merged.svg" width="250" height="36" '
            'alt="3 pull requests merged upstream" />' in row
        )
        assert (
            '<a href="https://github.com/ChrisTitusTech/winutil">'
            "<strong>ChrisTitusTech/winutil</strong></a> ★ 60.9k: "
            '<a href="https://github.com/ChrisTitusTech/winutil/pull/4992">#4992</a> · '
            '<a href="https://github.com/ChrisTitusTech/winutil/pull/4993">#4993</a> · '
            '<a href="https://github.com/ChrisTitusTech/winutil/pull/4995">#4995</a>' in row
        )
        assert "<strong>For everyone</strong>" in row
        assert "<em>Open source: showing up for the tools we share.</em>" in row
        assert 'upstream" />\n\n<br/>\n\n<a href=' in row

    def test_pr_limit_keeps_lowest_numbers(self):
        many = dict(WINUTIL, prs=[{"number": n, "html_url": f"u{n}"} for n in [9, 5, 7, 1, 3]])
        row = renderer.render_contrib_row([many], 5)
        assert "#1" in row
        assert "#7" in row
        assert "#9" not in row


class TestStatsLine:
    def test_exact_line(self):
        line = renderer.render_stats_line(
            13, ["C#", "JavaScript", "CSS"], datetime(2026, 8, 20, tzinfo=UTC)
        )
        expected = (
            '<p align="center"><code>13 original projects</code> '
            '<img src="assets/dot-gold.svg" width="10" height="10" alt="·" /> '
            "<code>C#</code> <code>JavaScript</code> <code>CSS</code> "
            '<img src="assets/dot-gold.svg" width="10" height="10" alt="·" /> '
            "<code>updated 2026-08-20</code></p>"
        )
        assert line == expected


class TestOssPill:
    def test_plural_label_and_alt(self):
        svg = renderer.render_oss_pill_svg(3)
        assert 'aria-label="3 pull requests merged upstream"' in svg
        assert ">3 PRs MERGED UPSTREAM<" in svg

    def test_singular(self):
        svg = renderer.render_oss_pill_svg(1)
        assert 'aria-label="1 pull request merged upstream"' in svg
        assert ">1 PR MERGED UPSTREAM<" in svg


class TestCompose:
    def test_structure_and_marker_wrap(self):
        block = renderer.compose(
            [("focus", [TIDSRO, IGNITE])],
            [WINUTIL],
            3,
            13,
            ["C#", "JavaScript", "CSS"],
            datetime(2026, 8, 20, tzinfo=UTC),
        )
        assert block.startswith('<table align="center">\n<tr>\n')
        assert block.count("<tr>") == 2
        assert block.rstrip().endswith("</p>")
        wrapped = renderer.wrap_with_markers(block)
        assert wrapped.startswith(renderer.MARKER_START + "\n")
        assert wrapped.endswith("\n" + renderer.MARKER_END)

    def test_no_contributions_omits_contrib_row(self):
        block = renderer.compose(
            [("focus", [TIDSRO])], [], 0, 13, ["C#"], datetime(2026, 8, 20, tzinfo=UTC)
        )
        assert "For everyone" not in block
        assert "oss-merged" not in block
