# TVMaze Show Finder

An automation that searches the [TVMaze API](https://www.tvmaze.com/api) for TV shows, lists the ones that meet a minimum rating and saves them to a report file (`tv_report.txt`). The search term and rating threshold come from `config.json`, so you can change its behaviour without editing code. Activity and errors are logged to `automation.log`.

Built step by step across the *AI Assisted Scripting: Low-code Pathway* labs. Each module adds a layer.

## Requirements
- Python 3.10 or later (tested on 3.14)
- Internet access to `api.tvmaze.com`
- `requests` (install with `pip install -r requirements.txt`)

## Usage
```bash
python main.py                          # web UI on http://localhost:8080 (opens the browser)
python main.py --port 9000              # web UI on another port
python main.py --no-browser             # start the server without opening a browser
python main.py --cli                    # command-line run using config.json
python main.py --cli --config other.json  # command-line run with a different config
```

### Web UI
Running `python main.py` starts the UI at **http://localhost:8080** and opens it in your browser. Press Ctrl+C to stop.

A Bootstrap 5 front end (`web/`) served by a small Python server (`tvmaze/web_server.py`). It uses the same API, filter and logging layers as the command-line tool, so web searches are also written to `automation.log`.

- Search box (press `/` to focus it), quick-search chips and a rating slider. Moving the slider re-filters the results straight away.
- Stats cards: search term, shows found, shows meeting the threshold, average rating.
- Poster cards with a rating badge, status, year, network and genres. Click a card for a details modal (summary and TVMaze link).
- Genre filter chips, a sort menu (rating, name, newest, relevance) and a "Show all results" switch.
- Dark/light theme toggle (remembered), loading skeletons, empty states and error toasts.
- Searches are kept in the URL (`?q=doctor&min_rating=7`), so a link opens the same results.

JSON API used by the page:
| Endpoint | Returns |
|---|---|
| `GET /api/config` | Default `search_term` and `minimum_rating` from `config.json` |
| `GET /api/search?q=<term>&min_rating=<0-10>` | `total_found`, `matching_count`, `average_rating`, and `shows` (each with a `meets_threshold` flag). Returns 400 for invalid input and 502 if TVMaze can't be reached. |

### Configuration (`config.json`)
```json
{
  "search_term": "comedy",
  "minimum_rating": 8
}
```
| Key | Type | Rules |
|---|---|---|
| `search_term` | string | Required and non-empty. Matches show **names**. |
| `minimum_rating` | number | 0–10. Unrated shows are always excluded. |
| `output_file` | string | Optional. The report file to write. Defaults to `tv_report.txt` in the current folder. |

### Example output
```
Show name                           Genre                          Rating
-------------------------------------------------------------------------
Doctor Who                          Drama, Adventure, Science-Fic     8.3
Doctor Foster                       Drama, Medical                    7.7
...
Summary
Search term      : doctor
Minimum rating   : 7.0
Shows found      : 10
Meet threshold   : 7
Average rating   : 7.7
```

## Project structure (layers by module)
| Module | Layer | Files |
|---|---|---|
| 2 | Planning | `docs/module2_automation_worksheet.md` |
| 3 | Presentation (welcome, results, summary) | `tvmaze/ui.py`, `docs/module3_prompts.md` |
| 4 | Clean code / refactoring | applied throughout, `docs/module4_refactoring.md` |
| 5 | API client + data model (JSON → `Show`) | `tvmaze/api_client.py`, `tvmaze/models.py`, `docs/module5_json_structure.md` |
| 6 | Configuration + business logic | `config.json`, `tvmaze/config.py`, `tvmaze/automation.py` |
| 7 | Testing + error handling | `tests/test_automation.py`, `tests/configs/`, `docs/module7_test_log.md` |
| 7/8 | Report output | `tvmaze/report.py`, `tv_report.txt` |
| 8 | Logging + documentation | `tvmaze/logging_setup.py`, `automation.log`, `README.md` |
| Extension | Web UI (Bootstrap, HTML, CSS, JS) | `main.py`, `tvmaze/web_server.py`, `web/index.html`, `web/css/styles.css`, `web/js/app.js` |

`main.py` is the entry point that wires the layers together.

## Logging
- Every run appends to `automation.log` (INFO and above): start, config loaded, API URL, result counts, finish.
- Errors are written to the log **and** printed to the console. The exit code is `1` on error and `0` on success.

| Situation | Logged message |
|---|---|
| Config file missing | `ERROR … Configuration file not found: <path>` |
| Invalid JSON / empty term / bad rating | `ERROR … <validation message>` |
| API unreachable / HTTP error | `ERROR … Unable to retrieve TV show data: <reason>` |
| Report file can't be written | `ERROR … Unable to create report file: <reason>` |
| Anything unexpected | `ERROR … Unexpected error` + full traceback |

Examples of errors logged successfully (from `automation.log`):
```
2026-10-29 09:28:53,898 | ERROR    | tvmaze.main | 'search_term' must be a non-empty string
2026-10-29 09:28:54,617 | ERROR    | tvmaze.main | Configuration file not found: tests/configs/missing.json
2026-10-29 09:28:55,126 | ERROR    | tvmaze.main | Unable to create report file: [Errno 2] No such file or directory: 'no_such_folder/tv_report.txt'
```

## Testing
```bash
python -m unittest discover -s tests -t . -v
```
The unit tests mock the API, so they run offline. See `docs/module7_test_log.md` for the full manual test log.

## Known limitations
- TVMaze search matches show names, not genres, and returns at most 10 results.
- Many shows have no rating; these never pass the rating filter.

*Documentation drafted with AI assistance (Claude) and checked against the code and real test runs.*
