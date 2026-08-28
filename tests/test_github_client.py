import requests

from src import github_client


class _Response:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class TestFetchRepoLanguages:
    def test_returns_the_language_byte_map(self, monkeypatch):
        monkeypatch.setattr(
            requests, "get", lambda *a, **k: _Response({"C#": 100, "TypeScript": 30})
        )
        assert github_client.fetch_repo_languages("malinfossum/varde", "t") == {
            "C#": 100,
            "TypeScript": 30,
        }

    def test_returns_empty_for_a_repo_with_no_detected_language(self, monkeypatch):
        monkeypatch.setattr(requests, "get", lambda *a, **k: _Response({}))
        assert github_client.fetch_repo_languages("malinfossum/getacademy", "t") == {}

    def test_survives_a_failed_request(self, monkeypatch, capsys):
        """One unreachable repo must not crash the run and leave the profile stale."""

        def boom(*a, **k):
            raise requests.RequestException("timeout")

        monkeypatch.setattr(requests, "get", boom)
        assert github_client.fetch_repo_languages("malinfossum/varde", "t") == {}
        assert "malinfossum/varde" in capsys.readouterr().err
