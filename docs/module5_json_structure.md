# Module 5: TVMaze API and JSON Structure

## Endpoint
`GET https://api.tvmaze.com/search/shows?q=<search term>`. No API key is required. It returns at most 10 results.

## JSON structure (explained with AI assistance)
The response is a **JSON array** (a Python `list`). Each element is an **object** (a Python `dict`) with two keys:

```json
[
  {
    "score": 0.676,
    "show": {
      "id": 18590,
      "name": "Comedy Connections",
      "type": "Documentary",
      "language": "English",
      "genres": ["Comedy"],
      "status": "Ended",
      "premiered": "2003-06-09",
      "rating": { "average": null },
      "network": { "name": "BBC One", "country": { "code": "GB" } },
      "summary": "<p>...</p>"
    }
  }
]
```

| Path | Python type | Notes |
|---|---|---|
| `[i]` | `dict` | One search match |
| `[i]["score"]` | `float` | How relevant the match is |
| `[i]["show"]` | `dict` | The show details |
| `[i]["show"]["name"]` | `str` | Show name |
| `[i]["show"]["genres"]` | `list[str]` | Can be empty `[]` |
| `[i]["show"]["rating"]["average"]` | `float` or `None` | **Often `null`** for less popular shows |
| `[i]["show"]["network"]` | `dict` or `None` | `None` for web-only shows |

### Things to watch for
- `rating.average` can be `null` → the code treats the show as *unrated* and excludes it from rating filters.
- `genres` can be empty → displayed as `N/A`.
- An unknown or empty search term returns `[]` with HTTP 200, not an error.

## Prompts used
- *Create a Python script that calls the TVMaze API, searches for TV shows, converts the JSON response into Python objects, and displays the show name, genre and rating for each result.*
- *Explain the JSON structure returned by the TVMaze search API. Show me how to access the show name, genres, and rating in Python.*

## How the project converts it
- `requests.get(...).json()` turns the response into Python lists and dicts (`tvmaze/api_client.py`).
- `Show.from_api()` turns each `"show"` dict into a `Show` dataclass with `name`, `genres` and `rating` (`tvmaze/models.py`). The rest of the code works with `Show` objects, not raw dicts.

## Sample output: `python main.py --cli --config tests/configs/valid.json` (search "doctor", minimum rating 7)
```
=========================================================================
 Welcome to the TVMaze Show Finder
=========================================================================
Show name                           Genre                          Rating
-------------------------------------------------------------------------
Doctor Who                          Drama, Adventure, Science-Fic     8.3
Doctor Who                          Action, Adventure, Science-Fi     8.4
Doctor Foster                       Drama, Medical                    7.7
Doctor Doctor                       Drama, Medical                    7.5
Good Doctor                         Drama, Romance, Medical           7.6
Doctor Thorne                       Drama                             7.4
Doctor Stranger                     Drama, Romance, Medical           7.3

Summary
-------------------------------------------------------------------------
Search term      : doctor
Minimum rating   : 7.0
Shows found      : 10
Meet threshold   : 7
Average rating   : 7.7

Report saved to tv_report.txt
```
