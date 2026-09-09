"""Tests for the orchestrator helpers that touch the filesystem."""

from __future__ import annotations

from src.main import _write_star_badges


class TestWriteStarBadges:
    def test_one_file_per_distinct_count(self, tmp_path):
        assert _write_star_badges(tmp_path, {1, 2, 60883}) is True
        names = sorted(p.name for p in tmp_path.iterdir())
        assert names == ["stars-1.svg", "stars-2.svg", "stars-60.9k.svg"]

    def test_rerun_with_same_counts_writes_nothing(self, tmp_path):
        _write_star_badges(tmp_path, {1, 2})
        assert _write_star_badges(tmp_path, {1, 2}) is False

    def test_stale_badge_is_pruned(self, tmp_path):
        _write_star_badges(tmp_path, {1, 2})
        assert _write_star_badges(tmp_path, {2}) is True
        assert sorted(p.name for p in tmp_path.iterdir()) == ["stars-2.svg"]

    def test_pruning_leaves_other_assets_alone(self, tmp_path):
        (tmp_path / "chip-gold.svg").write_text("<svg/>", encoding="utf-8")
        (tmp_path / "oss-merged.svg").write_text("<svg/>", encoding="utf-8")
        _write_star_badges(tmp_path, set())
        assert sorted(p.name for p in tmp_path.iterdir()) == ["chip-gold.svg", "oss-merged.svg"]
