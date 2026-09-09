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
            "&ensp;&nbsp;"
            '<img src="assets/stars-1.svg" width="31" height="26" align="middle" alt="1 star" />'
            "&ensp;&nbsp;a calm desktop timer &amp; alarm.\n\n"
            '<a href="https://github.com/malinfossum/ignite"><strong>ignite</strong></a>'
            "&ensp;&nbsp;"
            '<img src="assets/stars-1.svg" width="31" height="26" align="middle" alt="1 star" />'
            "&ensp;&nbsp;ADHD-friendly task app.\n\n"
            "</td>\n"
            "</tr>"
        )
        assert row == expected

    def test_zero_stars_omits_badge(self):
        row = renderer.render_group_row("wellbeing", [VARDE])
        assert "varde</strong></a>&ensp;&nbsp;a bilingual" in row
        assert "stars-0.svg" not in row


class TestContribRow:
    def test_pill_and_ascending_pr_links(self):
        row = renderer.render_contrib_row([WINUTIL], 3)
        assert (
            '<img src="assets/oss-merged.svg" width="250" height="36" '
            'alt="3 pull requests merged upstream" />' in row
        )
        assert (
            '<a href="https://github.com/ChrisTitusTech/winutil">'
            "<strong>ChrisTitusTech/winutil</strong></a>&ensp;&nbsp;"
            '<img src="assets/stars-60.9k.svg" width="53" height="26" '
            'align="middle" alt="60.9k stars" />&ensp;&nbsp;'
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


class TestStarBadge:
    def test_asset_name_shares_a_file_per_count(self):
        assert renderer.star_asset_name(1) == "stars-1.svg"
        assert renderer.star_asset_name(60883) == "stars-60.9k.svg"

    def test_svg_carries_label_and_accessible_name(self):
        svg = renderer.render_star_badge_svg(60883)
        assert 'aria-label="60.9k stars"' in svg
        assert ">60.9k</text>" in svg
        assert "#c9a96e" in svg

    def test_singular_star(self):
        assert 'aria-label="1 star"' in renderer.render_star_badge_svg(1)

    def test_width_matches_the_img_tag(self):
        svg = renderer.render_star_badge_svg(60883)
        assert f'width="{renderer.star_badge_width("60.9k")}"' in svg
        assert renderer.star_badge_width("60.9k") == 53
        assert renderer.star_badge_width("1") == 31

    def test_transparent_padding_lifts_the_capsule(self):
        # align="middle" centres the image on the baseline, so the capsule is
        # lifted by half the padding. Losing this silently drops it 4px.
        assert renderer.STAR_BADGE_HEIGHT == renderer.STAR_CAPSULE_HEIGHT + 8
        svg = renderer.render_star_badge_svg(1)
        assert 'viewBox="0 0 31 26"' in svg
        assert 'height="17"' in svg  # capsule rect, inset by the 0.5 stroke
        assert '<img src="assets/stars-1.svg" width="31" height="26" align="middle"' in (
            renderer._star_badge_img(1)
        )

    def test_no_separator_glyph(self):
        row = renderer.render_group_row("focus", [TIDSRO])
        assert renderer.GAP in row
        for dash in ("\u2014", "\u2013", ":"):
            assert f"</a>{dash}" not in row and f"/>{dash}" not in row

    def test_no_third_party_host(self):
        row = renderer.render_group_row("focus", [TIDSRO])
        assert "shields.io" not in row
        assert 'src="assets/' in row


class TestBadgeAlignment:
    """Geometry the eye notices but the markup does not show."""

    LABELS = ["1", "2", "999", "11.1k", "60.9k"]

    @staticmethod
    def _star_ink_bounds():
        coords = [
            tuple(float(n) for n in point.split())
            for point in renderer._STAR_PATH.replace("M", "").replace("Z", "").split("L")
            if point.strip()
        ]
        ys = [y for _, y in coords]
        xs = [x for x, _ in coords]
        return min(xs), max(xs), min(ys), max(ys)

    def test_star_ink_is_centred_on_the_capsule(self):
        # Not the star's geometric centre - its INK centre. A five-point star
        # reaches further up than down, so centring the geometry sits it high.
        _, _, top, bottom = self._star_ink_bounds()
        assert round((top + bottom) / 2, 2) == 9.0

    def test_digits_share_the_star_centre_line(self):
        # Digit cap ascent is 7.0 at font-size 11, so the cap centre is
        # baseline - 3.5. It has to land on the same y=9 as the star.
        assert renderer._TEXT_BASELINE - 7.0 / 2 == 9.0

    def test_star_to_number_gap_is_the_same_on_every_badge(self):
        _, ink_right, _, _ = self._star_ink_bounds()
        assert round(renderer._TEXT_X - ink_right, 2) == renderer._STAR_TEXT_GAP

    def test_side_padding_matches_on_both_edges(self):
        ink_left, _, _, _ = self._star_ink_bounds()
        for label in self.LABELS:
            right = renderer.star_badge_width(label) - renderer._TEXT_X
            right -= renderer._text_length(label)
            assert round(right, 2) == renderer._PAD_RIGHT, label
        assert abs(ink_left - renderer._PAD_RIGHT) < 0.05

    def test_text_length_is_pinned_so_fonts_cannot_shift_the_layout(self):
        svg = renderer.render_star_badge_svg(1)
        assert 'lengthAdjust="spacingAndGlyphs"' in svg
        assert f'textLength="{renderer._text_length("1"):g}"' in svg

    def test_narrow_and_wide_digits_do_not_share_a_width(self):
        # "1" is 3.85 wide and "0" is 6.04. A flat average is what made the
        # wide labels lopsided in the first place.
        assert renderer.star_badge_width("1") < renderer.star_badge_width("8")


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
