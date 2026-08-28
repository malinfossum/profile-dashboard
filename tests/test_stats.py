from collections import Counter

from src import stats


def _repo(**overrides):
    base = {
        "name": "demo",
        "language": "Python",
        "fork": False,
        "archived": False,
        "topics": [],
    }
    base.update(overrides)
    return base


class TestFilterActive:
    def test_keeps_normal_repos(self):
        repos = [_repo(name="a"), _repo(name="b")]
        assert stats.filter_active(repos) == repos

    def test_drops_forks(self):
        repos = [_repo(name="a"), _repo(name="b", fork=True)]
        assert [r["name"] for r in stats.filter_active(repos)] == ["a"]

    def test_drops_archived(self):
        repos = [_repo(name="a"), _repo(name="b", archived=True)]
        assert [r["name"] for r in stats.filter_active(repos)] == ["a"]


class TestCountRepos:
    def test_empty(self):
        assert stats.count_repos([]) == 0

    def test_counts(self):
        assert stats.count_repos([_repo(), _repo(), _repo()]) == 3


class TestTotalLanguageBytes:
    def test_sums_across_repos(self):
        breakdowns = [{"C#": 100, "TypeScript": 30}, {"C#": 50, "JavaScript": 20}]
        assert stats.total_language_bytes(breakdowns) == Counter(
            {"C#": 150, "TypeScript": 30, "JavaScript": 20}
        )

    def test_ignores_repos_with_no_detected_language(self):
        assert stats.total_language_bytes([{}, {"C#": 5}, {}]) == Counter({"C#": 5})

    def test_excludes_named_languages_case_insensitively(self):
        breakdowns = [{"C#": 100, "CSS": 90, "HTML": 80}]
        assert stats.total_language_bytes(breakdowns, exclude=["css", "Html"]) == Counter(
            {"C#": 100}
        )

    def test_empty_input(self):
        assert stats.total_language_bytes([]) == Counter()


class TestTopLanguages:
    def test_ranks_by_bytes_descending(self):
        counts = Counter({"C#": 300, "JavaScript": 200, "TypeScript": 100})
        assert stats.top_languages(counts) == ["C#", "JavaScript", "TypeScript"]

    def test_breaks_byte_ties_alphabetically(self):
        """Equal byte counts must not depend on dict order, or the pill flip-flops."""
        counts = Counter({"Python": 10, "CSS": 10, "HTML": 10})
        assert stats.top_languages(counts) == ["CSS", "HTML", "Python"]

    def test_respects_n_argument(self):
        counts = Counter({"A": 4, "B": 3, "C": 2, "D": 1})
        assert stats.top_languages(counts, n=2) == ["A", "B"]

    def test_empty_counts(self):
        assert stats.top_languages(Counter()) == []


class TestMostRecentFirst:
    def test_sorts_by_pushed_at_descending(self):
        repos = [
            _repo(name="old", pushed_at="2026-01-01T00:00:00Z"),
            _repo(name="new", pushed_at="2026-06-01T00:00:00Z"),
            _repo(name="mid", pushed_at="2026-03-01T00:00:00Z"),
        ]
        assert [r["name"] for r in stats.most_recent_first(repos)] == ["new", "mid", "old"]

    def test_missing_pushed_at_sorts_last(self):
        repos = [
            _repo(name="undated", pushed_at=None),
            _repo(name="dated", pushed_at="2026-01-01T00:00:00Z"),
        ]
        assert [r["name"] for r in stats.most_recent_first(repos)] == ["dated", "undated"]

    def test_does_not_mutate_input(self):
        repos = [
            _repo(name="a", pushed_at="2026-01-01T00:00:00Z"),
            _repo(name="b", pushed_at="2026-06-01T00:00:00Z"),
        ]
        stats.most_recent_first(repos)
        assert [r["name"] for r in repos] == ["a", "b"]


class TestDedupe:
    def test_removes_repeated_ids_keeping_first(self):
        repos = [_repo(name="a", id=1), _repo(name="b", id=2), _repo(name="a-dup", id=1)]
        assert [r["name"] for r in stats.dedupe(repos)] == ["a", "b"]

    def test_keeps_distinct_ids(self):
        repos = [_repo(id=1), _repo(id=2), _repo(id=3)]
        assert len(stats.dedupe(repos)) == 3


class TestGroupFeatured:
    def _repos(self):
        return [
            {"id": 1, "name": "tidsro", "full_name": "malinfossum/tidsro"},
            {"id": 2, "name": "ignite", "full_name": "malinfossum/ignite"},
            {"id": 3, "name": "wend", "full_name": "wendhq/wend"},
        ]

    def test_groups_follow_spec_order(self):
        from src.stats import group_featured

        grouped, leftovers = group_featured(
            self._repos(), [("focus", ["tidsro", "ignite"]), ("momentum", ["wendhq/wend"])]
        )
        assert [(k, [r["name"] for r in rs]) for k, rs in grouped] == [
            ("focus", ["tidsro", "ignite"]),
            ("momentum", ["wend"]),
        ]
        assert leftovers == []

    def test_unclaimed_repos_are_leftovers(self):
        from src.stats import group_featured

        grouped, leftovers = group_featured(self._repos(), [("focus", ["tidsro"])])
        assert [r["name"] for r in leftovers] == ["ignite", "wend"]

    def test_unknown_name_is_ignored(self):
        from src.stats import group_featured

        grouped, _ = group_featured(self._repos(), [("focus", ["nope", "tidsro"])])
        assert [r["name"] for r in grouped[0][1]] == ["tidsro"]


class TestGroupPrsByRepo:
    def test_groups_by_repository_url(self):
        from src.stats import group_prs_by_repo

        items = [
            {"number": 1, "repository_url": "https://api.github.com/repos/a/x"},
            {"number": 2, "repository_url": "https://api.github.com/repos/b/y"},
            {"number": 3, "repository_url": "https://api.github.com/repos/a/x"},
        ]
        grouped = group_prs_by_repo(items)
        assert sorted(grouped) == ["a/x", "b/y"]
        assert [p["number"] for p in grouped["a/x"]] == [1, 3]
