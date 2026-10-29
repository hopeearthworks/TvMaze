"""Tests for genre search mode (show index scan + disk cache)."""

import json
from unittest import mock

import pytest
import requests

from tvmaze import api_client
from tvmaze.config import ConfigError, load_config
from tvmaze.models import normalise_genre

INDEX_PAGE = [
    {"id": 1, "name": "Seinfeld", "genres": ["Comedy"], "rating": {"average": 8.6}},
    {"id": 2, "name": "Luther", "genres": ["Crime", "Drama"], "rating": {"average": 8.4}},
    {"id": 3, "name": "Friends", "genres": ["Comedy", "Romance"], "rating": {"average": 8.5}},
    {"id": 4, "name": "Unrated Sitcom", "genres": ["Comedy"], "rating": {"average": None}},
]


def page_response(payload, status_code=200):
    response = mock.Mock(status_code=status_code)
    response.json.return_value = payload
    if status_code == 404:
        response.raise_for_status.side_effect = requests.HTTPError(response=response)
    else:
        response.raise_for_status.return_value = None
    return response


@pytest.fixture
def index_api(tmp_path, monkeypatch):
    """One index page followed by a 404, with the disk cache in a temp folder."""
    monkeypatch.setattr(api_client, "CACHE_DIR", tmp_path)
    fake_get = mock.Mock(side_effect=[page_response(INDEX_PAGE), page_response(None, 404)])
    with mock.patch("requests.get", fake_get):
        yield fake_get


def test_genre_names_are_normalised():
    assert normalise_genre(" comedy ") == "Comedy"
    assert normalise_genre("science-fiction") == "Science-Fiction"
    with pytest.raises(ValueError, match="Unknown genre"):
        normalise_genre("sitcom")


def test_search_by_genre_returns_highest_rated_first(index_api):
    names = [show.name for show in api_client.search_by_genre("comedy")]
    assert names == ["Seinfeld", "Friends", "Unrated Sitcom"]
    assert index_api.call_count == 2  # page 0, then page 1 returned 404


def test_show_index_is_saved_and_reused_from_disk(index_api, tmp_path):
    api_client.search_by_genre("comedy")
    saved = json.loads((tmp_path / "show_index.json").read_text(encoding="utf-8"))
    assert len(saved["shows"]) == 4

    api_client.clear_cache()  # Forget the in-memory copy; the disk copy should be used.
    with mock.patch("requests.get") as fake_get:
        assert len(api_client.search_by_genre("crime")) == 1
    fake_get.assert_not_called()


def test_expired_disk_index_is_downloaded_again(index_api, tmp_path):
    (tmp_path / "show_index.json").write_text(json.dumps({"saved_at": 0, "shows": []}))
    assert len(api_client.search_by_genre("comedy")) == 3
    assert index_api.call_count == 2


def test_config_genre_mode_validates_genre(tmp_path):
    good = tmp_path / "good.json"
    good.write_text('{"search_term": "comedy", "search_mode": "genre", "minimum_rating": 8}')
    config = load_config(good)
    assert (config.search_term, config.search_mode) == ("Comedy", "genre")

    bad = tmp_path / "bad.json"
    bad.write_text('{"search_term": "sitcom", "search_mode": "genre", "minimum_rating": 8}')
    with pytest.raises(ConfigError, match="Unknown genre"):
        load_config(bad)


def test_config_rejects_unknown_search_mode(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"search_term": "comedy", "search_mode": "actor", "minimum_rating": 8}')
    with pytest.raises(ConfigError, match="search_mode"):
        load_config(bad)
