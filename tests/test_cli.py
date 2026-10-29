"""End-to-end tests for the command-line mode (main.run_cli), with the API mocked."""

import json
from unittest import mock

import pytest
import requests

import main

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
def write_config(tmp_path):
    """Write a config file into tmp_path and return its path."""

    def _write(**values):
        values.setdefault("output_file", str(tmp_path / "report.txt"))
        path = tmp_path / "config.json"
        path.write_text(json.dumps(values), encoding="utf-8")
        return path

    return _write


def test_successful_run_prints_results_and_saves_report(write_config, tmp_path, capsys):
    config = write_config(search_term="sherlock", minimum_rating=8)
    with mock.patch("requests.get", fake_get(SEARCH_RESULTS)):
        assert main.run_cli(config) == 0

    output = capsys.readouterr().out
    assert "Sherlock" in output
    assert "Meet threshold   : 1" in output
    report = (tmp_path / "report.txt").read_text(encoding="utf-8")
    assert "Name   : Sherlock" in report
    assert "Young Sherlock" not in report


def test_no_results_message(write_config, capsys):
    config = write_config(search_term="xyzzyqwerty", minimum_rating=5)
    with mock.patch("requests.get", fake_get([])):
        assert main.run_cli(config) == 0
    assert "No results were returned" in capsys.readouterr().out


def test_missing_config_returns_error_code(tmp_path):
    assert main.run_cli(tmp_path / "missing.json") == 1


def test_invalid_config_returns_error_code(write_config):
    assert main.run_cli(write_config(search_term="", minimum_rating=5)) == 1


def test_api_failure_returns_error_code(write_config, caplog):
    config = write_config(search_term="sherlock", minimum_rating=8)
    failing_get = mock.Mock(side_effect=requests.ConnectionError("no network"))
    with mock.patch("requests.get", failing_get):
        assert main.run_cli(config) == 1
    assert "Unable to retrieve TV show data" in caplog.text


def test_unwritable_report_returns_error_code(write_config, tmp_path, caplog):
    config = write_config(
        search_term="sherlock",
        minimum_rating=8,
        output_file=str(tmp_path / "no_such_folder" / "report.txt"),
    )
    with mock.patch("requests.get", fake_get(SEARCH_RESULTS)):
        assert main.run_cli(config) == 1
    assert "Unable to create report file" in caplog.text
