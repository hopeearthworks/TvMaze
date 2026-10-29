"""HTTP tests for the web layer: a real server on a random port, with TVMaze mocked.

The test client uses urllib (not requests) because requests.get is mocked.
"""

import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest import mock

import pytest
import requests

from tvmaze.web_server import RequestHandler

SEARCH_RESULTS = [
    {
        "score": 0.9,
        "show": {"id": 335, "name": "Sherlock", "genres": ["Crime"], "rating": {"average": 8.9}},
    },
    {
        "score": 0.8,
        "show": {
            "id": 1,
            "name": "Young Sherlock",
            "genres": ["Action"],
            "rating": {"average": 7.3},
        },
    },
]


def fake_get(payload):
    response = mock.Mock(status_code=200)
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return mock.Mock(return_value=response)


@pytest.fixture
def server(tmp_path, monkeypatch):
    """Start the web server on a free port and return its base URL."""
    config = tmp_path / "config.json"
    config.write_text('{"search_term": "sherlock", "minimum_rating": 8}', encoding="utf-8")
    monkeypatch.setattr(RequestHandler, "config_path", config)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), RequestHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()
    httpd.server_close()


def get(url):
    """Return (status, headers, body) without raising on HTTP errors."""
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.status, response.headers, response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        return error.code, error.headers, error.read().decode("utf-8")


def test_index_page_is_served(server):
    status, headers, body = get(server + "/")
    assert status == 200
    assert headers["Content-Type"].startswith("text/html")
    assert "ShowFinder" in body or "Show<span" in body


def test_page_uses_only_local_assets(server):
    _, _, body = get(server + "/")
    for cdn in ("cdn.jsdelivr", "googleapis", "gstatic", "unpkg", "cdnjs"):
        assert cdn not in body


@pytest.mark.parametrize(
    ("path", "content_type"),
    [
        ("/vendor/bootstrap/bootstrap.min.css", "text/css"),
        ("/vendor/bootstrap/bootstrap.bundle.min.js", "text/javascript"),
        ("/vendor/bootstrap-icons/fonts/bootstrap-icons.woff2?v=1", "font/woff2"),
        ("/vendor/fonts/plus-jakarta-sans-latin-wght-normal.woff2", "font/woff2"),
    ],
)
def test_vendor_assets_are_served_with_correct_types(server, path, content_type):
    status, headers, _ = get_bytes(server + path)
    assert status == 200
    assert headers["Content-Type"] == content_type


def get_bytes(url):
    with urllib.request.urlopen(url, timeout=5) as response:
        return response.status, response.headers, response.read()


@pytest.mark.parametrize("path", ["/../main.py", "/..%2Fconfig.json", "/missing.css"])
def test_files_outside_web_folder_are_not_served(server, path):
    assert get(server + path)[0] == 404


def test_config_endpoint_returns_defaults_and_genres(server):
    status, _, body = get(server + "/api/config")
    data = json.loads(body)
    assert status == 200
    assert data["search_term"] == "sherlock"
    assert data["search_mode"] == "name"
    assert "Comedy" in data["genres"]


def test_search_endpoint_flags_matching_shows(server):
    with mock.patch("requests.get", fake_get(SEARCH_RESULTS)):
        status, _, body = get(server + "/api/search?q=sherlock&min_rating=8")
    data = json.loads(body)
    assert status == 200
    assert (data["total_found"], data["matching_count"], data["average_rating"]) == (2, 1, 8.9)
    assert [show["meets_threshold"] for show in data["shows"]] == [True, False]


@pytest.mark.parametrize(
    "query",
    [
        "q=&min_rating=8",
        "q=x&min_rating=abc",
        "q=x&min_rating=11",
        "q=x&mode=actor",
        "q=sitcom&mode=genre",
    ],
)
def test_invalid_search_requests_return_400(server, query):
    status, _, body = get(server + "/api/search?" + query)
    assert status == 400
    assert "error" in json.loads(body)


def test_api_outage_returns_502(server):
    with mock.patch("requests.get", side_effect=requests.ConnectionError("down")):
        status, _, body = get(server + "/api/search?q=sherlock&min_rating=8")
    assert status == 502
    assert "TVMaze" in json.loads(body)["error"]


def test_csv_report_download(server):
    with mock.patch("requests.get", fake_get(SEARCH_RESULTS)):
        status, headers, body = get(server + "/api/report?q=sherlock&min_rating=8&format=csv")
    assert status == 200
    assert headers["Content-Disposition"] == 'attachment; filename="tv_report_sherlock.csv"'
    assert body.splitlines()[1].startswith("Sherlock,Crime,8.9")


def test_show_details_bad_id_returns_400(server):
    assert get(server + "/api/show?id=abc")[0] == 400


def test_unknown_show_returns_404(server):
    not_found = mock.Mock(status_code=404)
    not_found.raise_for_status.side_effect = requests.HTTPError(response=not_found)
    with mock.patch("requests.get", return_value=not_found):
        assert get(server + "/api/show?id=999999")[0] == 404
