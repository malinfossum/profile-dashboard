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


class TestTopLanguages:
    def test_top_three_by_repo_count(self):
        repos = [
            _repo(language="Python"),
            _repo(language="Python"),
            _repo(language="JavaScript"),
            _repo(language="JavaScript"),
            _repo(language="JavaScript"),
            _repo(language="HTML"),
        ]
        assert stats.top_languages(repos) == ["JavaScript", "Python", "HTML"]

    def test_skips_null_language(self):
        repos = [_repo(language=None), _repo(language="Python")]
        assert stats.top_languages(repos) == ["Python"]

    def test_respects_n_argument(self):
        repos = [
            _repo(language="A"),
            _repo(language="B"),
            _repo(language="C"),
            _repo(language="D"),
        ]
        assert len(stats.top_languages(repos, n=2)) == 2

    def test_empty_repos(self):
        assert stats.top_languages([]) == []
