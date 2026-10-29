"""Tests for API response caching and rate-limit retries."""

from unittest import mock

from tvmaze import api_client


def make_response(payload, status_code=200):
    response = mock.Mock(status_code=status_code)
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_repeat_search_is_served_from_cache():
    fake_get = mock.Mock(return_value=make_response([]))
    with mock.patch("requests.get", fake_get):
        api_client.search_shows("Sherlock")
        api_client.search_shows("sherlock ")  # Same search, different case/spacing.
    assert fake_get.call_count == 1


def test_expired_cache_entry_is_refetched():
    fake_get = mock.Mock(return_value=make_response([]))
    with mock.patch("requests.get", fake_get), mock.patch.object(api_client, "CACHE_TTL_SECONDS", 0):
        api_client.search_shows("sherlock")
        api_client.search_shows("sherlock")
    assert fake_get.call_count == 2


def test_rate_limited_request_is_retried():
    fake_get = mock.Mock(side_effect=[make_response(None, 429), make_response([])])
    with mock.patch("requests.get", fake_get), mock.patch("time.sleep") as fake_sleep:
        assert api_client.search_shows("sherlock") == []
    assert fake_get.call_count == 2
    fake_sleep.assert_called_once()
