import pytest

from src.readme_writer import MarkersMissingError, write_block


def _readme_with_markers(body: str = "OLD") -> str:
    return (
        "# malinfossum\n"
        "\n"
        "Some intro text.\n"
        "\n"
        "<!-- DASHBOARD:START -->\n"
        f"{body}\n"
        "<!-- DASHBOARD:END -->\n"
        "\n"
        "More content below.\n"
    )


def test_replaces_block_between_markers(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(_readme_with_markers("OLD"), encoding="utf-8")

    new_block = "<!-- DASHBOARD:START -->\nNEW\n<!-- DASHBOARD:END -->"
    changed = write_block(readme, new_block)

    assert changed is True
    content = readme.read_text(encoding="utf-8")
    assert "NEW" in content
    assert "OLD" not in content
    assert "Some intro text." in content
    assert "More content below." in content


def test_returns_false_when_unchanged(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(_readme_with_markers("KEEP"), encoding="utf-8")

    new_block = "<!-- DASHBOARD:START -->\nKEEP\n<!-- DASHBOARD:END -->"
    changed = write_block(readme, new_block)

    assert changed is False


def test_dry_run_does_not_write(tmp_path):
    readme = tmp_path / "README.md"
    original = _readme_with_markers("ORIGINAL")
    readme.write_text(original, encoding="utf-8")

    new_block = "<!-- DASHBOARD:START -->\nNEW\n<!-- DASHBOARD:END -->"
    changed = write_block(readme, new_block, dry_run=True)

    assert changed is True
    assert readme.read_text(encoding="utf-8") == original


def test_missing_markers_raises(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("# no markers here\n", encoding="utf-8")

    with pytest.raises(MarkersMissingError):
        write_block(readme, "<!-- DASHBOARD:START -->\nx\n<!-- DASHBOARD:END -->")


def test_only_one_marker_raises(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("# title\n<!-- DASHBOARD:START -->\nbody\n", encoding="utf-8")

    with pytest.raises(MarkersMissingError):
        write_block(readme, "<!-- DASHBOARD:START -->\nx\n<!-- DASHBOARD:END -->")


class TestWriteTextFile:
    def test_writes_new_file(self, tmp_path):
        from src.readme_writer import write_text_file

        target = tmp_path / "pill.svg"
        assert write_text_file(target, "<svg/>") is True
        assert target.read_text(encoding="utf-8") == "<svg/>"

    def test_idempotent_when_unchanged(self, tmp_path):
        from src.readme_writer import write_text_file

        target = tmp_path / "pill.svg"
        target.write_text("<svg/>", encoding="utf-8")
        assert write_text_file(target, "<svg/>") is False

    def test_dry_run_does_not_write(self, tmp_path):
        from src.readme_writer import write_text_file

        target = tmp_path / "pill.svg"
        assert write_text_file(target, "<svg/>", dry_run=True) is True
        assert not target.exists()
