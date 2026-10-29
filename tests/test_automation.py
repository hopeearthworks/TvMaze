"""Test layer (Module 7): automated tests for the TVMaze automation.

The API is mocked so these tests run offline and give repeatable results.
Run with:  python -m unittest discover -s tests -t . -v
"""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import requests

from tvmaze import api_client, automation, web_server
from tvmaze.config import Config, ConfigError, load_config
from tvmaze.models import Show
from tvmaze.report import save_report

CONFIG_DIR = Path(__file__).parent / "configs"

SAMPLE_RESPONSE = [
    {"score": 0.9, "show": {"name": "Sherlock", "genres": ["Crime"], "rating": {"average": 8.9}}},
    {"score": 0.8, "show": {"name": "Young Sherlock", "genres": ["Action"], "rating": {"average": 7.3}}},
    {"score": 0.7, "show": {"name": "Sherlock Hound", "genres": [], "rating": {"average": None}}},
]


def fake_get(payload):
    """Return a mock requests.get whose response JSON is the given payload."""
    response = mock.Mock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return mock.Mock(return_value=response)


class ConfigTests(unittest.TestCase):

    def test_valid_config_loads(self):
        config = load_config(CONFIG_DIR / "valid.json")
        self.assertEqual(config, Config("doctor", 7.0, "tv_report.txt"))

    def test_empty_search_term_rejected(self):
        with self.assertRaisesRegex(ConfigError, "non-empty"):
            load_config(CONFIG_DIR / "empty_term.json")

    def test_missing_config_file_rejected(self):
        with self.assertRaisesRegex(ConfigError, "not found"):
            load_config(CONFIG_DIR / "does_not_exist.json")


class ApiClientTests(unittest.TestCase):

    def test_valid_search_returns_show_objects(self):
        with mock.patch("requests.get", fake_get(SAMPLE_RESPONSE)):
            shows = api_client.search_shows("sherlock")
        self.assertEqual(len(shows), 3)
        self.assertEqual(shows[0], Show("Sherlock", ["Crime"], 8.9))
        self.assertIsNone(shows[2].rating)

    def test_invalid_search_returns_no_shows(self):
        with mock.patch("requests.get", fake_get([])):
            self.assertEqual(api_client.search_shows("xyzzyqwerty"), [])

    def test_empty_search_term_raises(self):
        with self.assertRaises(ValueError):
            api_client.search_shows("   ")

    def test_api_failure_raises_request_exception(self):
        failing_get = mock.Mock(side_effect=requests.ConnectionError("no network"))
        with mock.patch("requests.get", failing_get):
            with self.assertRaises(requests.RequestException):
                api_client.search_shows("sherlock")


class FilterTests(unittest.TestCase):

    def setUp(self):
        self.shows = [Show.from_api(result["show"]) for result in SAMPLE_RESPONSE]

    def test_threshold_keeps_rated_shows_only(self):
        names = [show.name for show in automation.filter_by_rating(self.shows, 7)]
        self.assertEqual(names, ["Sherlock", "Young Sherlock"])

    def test_high_threshold_returns_nothing(self):
        self.assertEqual(automation.filter_by_rating(self.shows, 9.5), [])

    def test_meets_threshold_rule(self):
        self.assertTrue(automation.meets_threshold(Show("A", rating=8.0), 8))  # boundary
        self.assertFalse(automation.meets_threshold(Show("B", rating=7.9), 8))
        self.assertFalse(automation.meets_threshold(Show("C", rating=None), 0))


class ReportTests(unittest.TestCase):

    def test_report_written(self):
        with tempfile.TemporaryDirectory() as folder:
            report_file = Path(folder) / "report.txt"
            save_report([Show("Sherlock", ["Crime"], 8.9)], "sherlock", 8, report_file)
            content = report_file.read_text(encoding="utf-8")
        self.assertIn("Name   : Sherlock", content)
        self.assertIn("Rating : 8.9", content)

    def test_report_in_missing_folder_raises(self):
        with self.assertRaises(OSError):
            save_report([], "sherlock", 8, Path("no_such_folder") / "report.txt")


class WebServerTests(unittest.TestCase):

    def test_rating_must_be_between_0_and_10(self):
        self.assertEqual(web_server.parse_minimum_rating("7.5"), 7.5)
        for bad_value in ("abc", "11", "-1"):
            with self.assertRaises(ValueError):
                web_server.parse_minimum_rating(bad_value)

    def test_search_response_flags_matching_shows(self):
        with mock.patch("requests.get", fake_get(SAMPLE_RESPONSE)):
            data = web_server.build_search_response("sherlock", 8)
        self.assertEqual(data["total_found"], 3)
        self.assertEqual(data["matching_count"], 1)
        self.assertEqual(data["average_rating"], 8.9)
        self.assertEqual([show["meets_threshold"] for show in data["shows"]], [True, False, False])


if __name__ == "__main__":
    unittest.main()
