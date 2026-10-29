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
| 8 | Default config | `config.json`: `"comedy"`, genre mode, min 8 | Runs without code changes and returns real comedies | 671 comedies found, 91 rated 8 or above (Rick and Morty 8.7, The IT Crowd 8.7, Fargo 8.6, …); report saved | **Pass** |

> **Observation (test 8):** At first this test returned 0 shows. TVMaze's search matches show *titles*, so `"comedy"` found shows with "Comedy" in the name, most of them unrated. Adding a `"search_mode": "genre"` option, which scans TVMaze's show index, fixed this; the result above is the re-test.

## Issues found and fixed during development
The course's model answer lists typical failures in a first-draft script. Each one is handled in this project, and the related test above was re-run after the fix:

| Issue | Fix | Re-test |
|---|---|---|
| Blank search terms not validated | `config.load_config` rejects an empty `search_term` | Test 3: Pass |
| Missing config.json causes a traceback | `ConfigError` caught in `main.py`, logged | Test 5: Pass |
| User not told when nothing matches | Separate "no results" / "none met the minimum rating" messages (`ui.display_shows`) | Tests 2 and 4: Pass |
| API connection failures not handled | `timeout=10`, `raise_for_status()`, `requests.RequestException` caught | Test 7: Pass |
| File creation errors not handled | `OSError` from `report.save_report` caught and logged | Test 6: Pass |

## Automated tests (pytest, API mocked)
Command: `python -m pytest --cov`. The suite started as 11 `unittest` tests and grew as the project gained features.

| File | Tests | Covers |
|---|---|---|
| `test_automation.py` | 14 | Config validation, JSON → `Show`, invalid/empty terms, API failure, rating filter and boundary (8.0 meets 8), report file errors |
| `test_cli.py` | 6 | `main.py --cli` end to end: success + report, no results, missing/invalid config, API outage, unwritable report (each returns the right exit code and logs the error) |
| `test_web_server.py` | 20 | Real HTTP server on a random port: pages, vendor assets and MIME types, path traversal blocked, search, 400/404/502 errors, CSV download |
| `test_genre_search.py` | 6 | Genre normalisation, genre filter order, show-index disk cache save/reuse/expiry, genre config validation |
| `test_show_details.py` | 7 | Cast + next episode extraction, invalid show IDs |
| `test_api_cache.py` | 3 | Cache hits, cache expiry, HTTP 429 retry |
| `test_report.py` | 3 | Text report, CSV report, CSV formula neutralising |

```
59 passed in 11.60s
TOTAL coverage: 85%
```

Static checks: `ruff check .` reports *All checks passed!*; `mypy` reports *Success: no issues found in 10 source files*.
## Copilot prompts used for testing
- *Suggest normal, boundary and invalid test cases for this TVMaze automation.*
- *Review this script and identify any missing input validation or error handling.*
- *Explain this error message and suggest a safe fix.*
