"""Tests for the show details (cast + next episode) lookup."""

from unittest import mock

import pytest

from tvmaze import api_client
from tvmaze.web_server import parse_show_id

SHOW_WITH_EMBEDS = {
    "id": 335,
    "name": "Sherlock",
    "_embedded": {
        "cast": [
            {"person": {"name": "Benedict Cumberbatch", "image": {"medium": "http://img/bc.jpg"}},
             "character": {"name": "Sherlock Holmes"}},
            {"person": {"name": "Martin Freeman", "image": None},
             "character": {"name": "Dr John Watson"}},
        ],
        "nextepisode": {"name": "The Return", "season": 5, "number": 1, "airdate": "2027-01-01"},
    },
}


def fake_get(payload):
    response = mock.Mock(status_code=200)
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return mock.Mock(return_value=response)


def test_show_details_extracts_cast_and_next_episode():
    with mock.patch("requests.get", fake_get(SHOW_WITH_EMBEDS)) as get:
        details = api_client.get_show_details(335)
    assert get.call_args.kwargs["params"] == {"embed[]": ["cast", "nextepisode"]}
    assert details["cast"][0] == {"name": "Benedict Cumberbatch", "character": "Sherlock Holmes",
                                  "image": "http://img/bc.jpg"}
    assert details["cast"][1]["image"] is None
    assert details["next_episode"]["season"] == 5


def test_show_without_embeds_has_empty_cast_and_no_next_episode():
    with mock.patch("requests.get", fake_get({"id": 1, "name": "Old Show"})):
        details = api_client.get_show_details(1)
    assert details == {"id": 1, "cast": [], "next_episode": None}


@pytest.mark.parametrize("value", ["", "abc", "0", "-5", "1.5"])
def test_invalid_show_ids_are_rejected(value):
    with pytest.raises(ValueError):
        parse_show_id({"id": [value]})
