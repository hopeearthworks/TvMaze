# Module 7: Test Log

**System under test:** `main.py` (TVMaze automation)  
**Date:** 2026-10-29  
**Environment:** Windows 11, Python 3.14.3, requests 2.34.2, live TVMaze API  
**Method:** `python main.py --cli --config <config file>` with the scenario configs in `tests/configs/`

## Manual / end-to-end tests

| # | Test | Input (config) | Expected result | Actual result | Pass/Fail |
|---|---|---|---|---|---|
| 1 | Valid search term | `valid.json`: `"doctor"`, min 7 | API returns matching shows; only shows rated ≥ 7 listed; report saved; exit 0 | 10 found, 7 listed (Doctor Who 8.3/8.4, Doctor Foster 7.7, …), average 7.7, `tv_report.txt` written, exit 0 | **Pass** |
| 2 | Invalid search term | `invalid_term.json`: `"xyzzyqwerty"`, min 5 | No crash; user told no results were returned | "No results were returned for this search term."; 0 found; exit 0 | **Pass** |
| 3 | Empty search term | `empty_term.json`: `""`, min 5 | Rejected before calling the API; clear error; logged | `ERROR: 'search_term' must be a non-empty string`; logged; exit 1 | **Pass** |
| 4 | High rating threshold | `high_threshold.json`: `"sherlock"`, min 9.5 | No shows meet the threshold; user told so | "No shows met the minimum rating."; 10 found, 0 meet (top is Sherlock 8.9); exit 0 | **Pass** |
| 5 | Missing configuration file | `missing.json` (doesn't exist) | Helpful error message, no traceback; logged | `ERROR: Configuration file not found: tests/configs/missing.json`; logged; exit 1 | **Pass** |
| 6 | Report file cannot be created | `bad_output.json`: `output_file` in a folder that doesn't exist | File error handled separately from input/API errors; logged | `ERROR: Unable to create report file: [Errno 2] No such file or directory…`; logged; exit 1 | **Pass** |
| 7 | API connection failure | Network failure simulated (unit test, `requests.get` raises `ConnectionError`) | Handled as `RequestException`, not a crash | `RequestException` raised by the API layer; `main.py` logs "Unable to retrieve TV show data" | **Pass** |
| 8 | Default config | `config.json`: `"comedy"`, min 8 | Runs without code changes | 10 found, 0 meet the threshold (all comedy results are unrated); report saved | **Pass** |

> **Observation (test 8):** TVMaze's search matches show *names*, not genres, so `"comedy"` returns shows with "Comedy" in the title. Most of them have no rating.

## Issues found and fixed during development
The course's model answer lists typical failures in a first-draft script. Each one is handled in this project, and the related test above was re-run after the fix:

| Issue | Fix | Re-test |
|---|---|---|
| Blank search terms not validated | `config.load_config` rejects an empty `search_term` | Test 3: Pass |
| Missing config.json causes a traceback | `ConfigError` caught in `main.py`, logged | Test 5: Pass |
| User not told when nothing matches | Separate "no results" / "none met the minimum rating" messages (`ui.display_shows`) | Tests 2 and 4: Pass |
| API connection failures not handled | `timeout=10`, `raise_for_status()`, `requests.RequestException` caught | Test 7: Pass |
| File creation errors not handled | `OSError` from `report.save_report` caught and logged | Test 6: Pass |

## Automated unit tests (`tests/test_automation.py`, API mocked)
Command: `python -m unittest discover -s tests -t . -v`

| Test | Covers | Result |
|---|---|---|
| `test_valid_config_loads` | Valid config (incl. default `output_file`) | Pass |
| `test_empty_search_term_rejected` | Empty term (config) | Pass |
| `test_missing_config_file_rejected` | Missing config | Pass |
| `test_valid_search_returns_show_objects` | Valid term, JSON → `Show` | Pass |
| `test_invalid_search_returns_no_shows` | Invalid term | Pass |
| `test_empty_search_term_raises` | Empty term (API layer) | Pass |
| `test_api_failure_raises_request_exception` | API connection failure | Pass |
| `test_threshold_keeps_rated_shows_only` | Filter excludes unrated shows | Pass |
| `test_high_threshold_returns_nothing` | High threshold | Pass |
| `test_report_written` | Report file contents | Pass |
| `test_report_in_missing_folder_raises` | File creation error | Pass |

```
Ran 11 tests in 0.005s

OK
```

## Copilot prompts used for testing
- *Suggest normal, boundary and invalid test cases for this TVMaze automation.*
- *Review this script and identify any missing input validation or error handling.*
- *Explain this error message and suggest a safe fix.*
