# TVMaze Show Finder

An automation that searches the [TVMaze API](https://www.tvmaze.com/api) for TV shows by **title** or by **genre**, lists the ones that meet a minimum rating and saves them to a report file (`tv_report.txt`). The search and rating threshold come from `config.json`, so you can change its behaviour without editing code. Activity and errors are logged to `automation.log`.

Built step by step across the *AI Assisted Scripting: Low-code Pathway* labs. Each module adds a layer.

## Requirements
- Python 3.10 or later (tested on 3.14)
- Internet access to `api.tvmaze.com`
- `pip install -r requirements.txt` (just `requests`)
- For development: `pip install -r requirements-dev.txt` (pytest, coverage, ruff, mypy)

## Usage
```bash
python main.py                            # web UI on http://localhost:8080 (opens the browser)
python main.py --port 9000                # web UI on another port
python main.py --no-browser               # start the server without opening a browser
python main.py --cli                      # command-line run using config.json
python main.py --cli --config other.json  # command-line run with a different config
```

### Web UI
Running `python main.py` starts the UI at **http://localhost:8080** and opens it in your browser. Press Ctrl+C to stop.

A Bootstrap 5 front end (`web/`) served by a small Python server (`tvmaze/web_server.py`). It uses the same search, rating filter, report and logging layers as the command-line tool. Bootstrap, the icons and the font are stored in `web/vendor/`, so the page doesn't depend on any CDN.

- **Title or genre search.** A toggle switches between a search box and a genre dropdown. Press `/` to jump to the search box. Quick-search chips cover both modes.
- **Rating slider.** The server re-checks the threshold shortly after you stop moving the slider.
- **Stats cards.** Search term or genre, shows found, shows meeting the threshold, average rating.
- **Poster cards.** Rating badge, status, year, network and genres, with "Load more" paging for large genre results.
- **Details pop-up.** Summary, cast, next episode (when one is scheduled) and a TVMaze link.
- **Watchlist.** Bookmark shows from a card or the pop-up; a slide-out panel lists them. It is saved in this browser only.
- **Report download.** The **Report** menu downloads the current results as `.txt` or `.csv`.
- **Filters.** Genre filter chips, a sort menu (rating, name, newest, relevance) and a "Show all results" switch.
- **Polish.** Dark/light theme (remembered), loading skeletons, empty states, error toasts. Searches are kept in the URL (`?q=Comedy&mode=genre&min_rating=8`), so a link reopens the same results.

JSON API used by the page:

| Endpoint | Returns |
|---|---|
| `GET /api/config` | Default `search_term`, `search_mode` and `minimum_rating` from `config.json`, plus the list of `genres`. |
| `GET /api/search?q=<term>&mode=<name\|genre>&min_rating=<0-10>` | `total_found`, `matching_count`, `average_rating`, and `shows` (each with a `meets_threshold` flag). |
| `GET /api/report?<search params>&format=<txt\|csv>` | The matching shows as a downloadable file. |
| `GET /api/show?id=<TVMaze ID>` | `cast` (up to 12) and `next_episode` for one show. |

Errors come back as JSON `{"error": "..."}` with status 400 (invalid input), 404 (unknown show) or 502 (TVMaze unreachable).

### Configuration (`config.json`)
```json
{
  "search_term": "comedy",
  "search_mode": "genre",
  "minimum_rating": 8
}
```
| Key | Type | Rules |
|---|---|---|
| `search_term` | string | Required. In `name` mode it is matched against show titles; in `genre` mode it must be a TVMaze genre (e.g. Comedy, Crime, Drama, Science-Fiction). |
| `search_mode` | string | Optional. `name` (default) or `genre`. |
| `minimum_rating` | number | 0–10. Unrated shows are always excluded. |
| `output_file` | string | Optional. The report file to write. Defaults to `tv_report.txt` in the current folder. |

**How genre mode works:** TVMaze's search endpoint only matches titles. Genre mode downloads the first 10 pages of TVMaze's show index (about 2,500 shows, which include most well-known series) and filters them by genre. The index is saved to `.cache/show_index.json` for 24 hours. The first genre search takes about 10–15 seconds; after that it is instant.

### Example output (`python main.py --cli`, Comedy rated 8 or above)
```
Show name                           Genre                          Rating
-------------------------------------------------------------------------
Rick and Morty                      Comedy, Adventure, Science-Fi     8.7
The IT Crowd                        Comedy                            8.7
Fargo                               Drama, Comedy, Crime              8.6
...
Summary
Search genre     : Comedy
Minimum rating   : 8.0
Shows found      : 671
Meet threshold   : 91
Average rating   : 8.1
```

## Project structure (layers by module)
| Module | Layer | Files |
|---|---|---|
| 2 | Planning | `docs/module2_automation_worksheet.md` |
| 3 | Presentation (welcome, results, summary) | `tvmaze/ui.py`, `docs/module3_prompts.md` |
| 4 | Clean code / refactoring | applied throughout, `docs/module4_refactoring.md` |
| 5 | API client + data model (JSON → `Show`) | `tvmaze/api_client.py`, `tvmaze/models.py`, `docs/module5_json_structure.md` |
| 6 | Configuration + business logic | `config.json`, `tvmaze/config.py`, `tvmaze/automation.py` |
| 7 | Testing + error handling | `tests/`, `tests/configs/`, `docs/module7_test_log.md` |
| 7/8 | Report output (.txt / .csv) | `tvmaze/report.py`, `tv_report.txt` |
| 8 | Logging + documentation | `tvmaze/logging_setup.py`, `automation.log`, `README.md`, `docs/evidence/` |
| Extension | Web UI (Bootstrap, HTML, CSS, JS) | `main.py`, `tvmaze/web_server.py`, `web/` |

`main.py` is the entry point that wires the layers together.

## Logging
- Every run appends to `automation.log` (INFO and above): start, config loaded, API calls, cache hits, result counts, finish.
- The log rotates at 1 MB and keeps 5 old files (`automation.log.1` … `.5`).
- Errors are written to the log **and** printed to the console. In `--cli` mode the exit code is `1` on error and `0` on success.
- `automation.log` and `tv_report.txt` are not committed to git. Sample copies for the Module 8 deliverable are in `docs/evidence/`.

| Situation | Logged message |
|---|---|
| Config file missing | `ERROR … Configuration file not found: <path>` |
| Invalid JSON / empty term / unknown genre / bad rating | `ERROR … <validation message>` |
| API unreachable / HTTP error | `ERROR … Unable to retrieve TV show data: <reason>` |
| TVMaze rate limit (HTTP 429) | `WARNING … TVMaze rate limit reached; retrying in 2s` |
| Report file can't be written | `ERROR … Unable to create report file: <reason>` |
| Anything unexpected | `ERROR … Unexpected error` + full traceback |

Examples of errors logged successfully (from `docs/evidence/automation_sample.log`):
```
2026-10-29 09:28:53,898 | ERROR    | tvmaze.main | 'search_term' must be a non-empty string
2026-10-29 09:28:54,617 | ERROR    | tvmaze.main | Configuration file not found: tests/configs/missing.json
2026-10-29 09:28:55,126 | ERROR    | tvmaze.main | Unable to create report file: [Errno 2] No such file or directory: 'no_such_folder/tv_report.txt'
```

## Performance
- **API cache.** Responses are cached in memory for 10 minutes (up to 200 entries), so repeat searches and slider changes don't call TVMaze again.
- **Rate limits.** TVMaze allows about 20 calls per 10 seconds. A rate-limited call (HTTP 429) is retried up to twice.

## Development
```bash
python -m pytest                # 59 tests; the TVMaze API is mocked, so they run offline
python -m pytest --cov          # with a coverage report (~85%)
ruff check . && ruff format .   # lint + format (settings in pyproject.toml)
mypy                            # type check tvmaze/ and main.py
```
The tests cover the config, API client, cache, genre index, filters, reports, the CLI end to end (`tests/test_cli.py`) and the HTTP server on a random port (`tests/test_web_server.py`). See `docs/module7_test_log.md` for the manual test log.

## Known limitations
- Title search returns at most 10 results (a TVMaze limit).
- Genre mode only covers the first ~2,500 shows in TVMaze's index. Raise `INDEX_PAGES` in `tvmaze/api_client.py` to scan more, at the cost of a slower first run.
- Many shows have no rating; these never pass the rating filter.
- The web server (`http.server`) is meant for local use. For a shared deployment, move the web layer to Flask or FastAPI.

*Documentation drafted with AI assistance (Claude) and checked against the code and real test runs.*
