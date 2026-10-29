# Module 4: Improving AI-Generated Code

## Script received
```python
a = input("Enter a search term: ")
print(f"Searching for {a}")
data = ["Doctor Who", "Sherlock", "Luther"]
for s in data:
print(s)
print("Done")
```

## Issues identified
| Category | Issue |
|---|---|
| Poor variable names | `a`, `data` and `s` don't say what they hold. |
| Missing comments | There is no docstring or comment explaining what the script is for. |
| Missing functions | Everything runs at module level, so nothing can be reused or tested. There is no `main()`. |
| Readability / bugs | The loop body isn't indented (`IndentationError`). The search term is never used, so every show is printed. Empty input is accepted. There is no "no results" message. |

## Refactored script
```python
"""Search a list of TV shows by name."""

AVAILABLE_SHOWS = ["Doctor Who", "Sherlock", "Luther"]


def get_search_term():
    """Prompt the user for a non-empty search term."""
    search_term = input("Enter a search term: ").strip()
    while not search_term:
        search_term = input("Search term cannot be empty. Try again: ").strip()
    return search_term


def find_matching_shows(search_term, shows):
    """Return the shows whose names contain the search term (case-insensitive)."""
    return [show for show in shows if search_term.lower() in show.lower()]


def display_results(matching_shows):
    """Print each matching show, or a message if there are none."""
    if not matching_shows:
        print("No matching shows found.")
        return
    for show_name in matching_shows:
        print(f"- {show_name}")


def main():
    search_term = get_search_term()
    print(f"Searching for '{search_term}'...")
    display_results(find_matching_shows(search_term, AVAILABLE_SHOWS))
    print("Done")


if __name__ == "__main__":
    main()
```

Tested: an empty input is rejected and re-prompted; `doc` returns `- Doctor Who`.

## How this was applied to the project
The same principles were applied to every layer of the TVMaze project:
- Descriptive names (`search_term`, `matching_shows`, `minimum_rating`).
- One job per function, each with a docstring.
- One responsibility per module: `ui`, `models`, `api_client`, `config`, `automation`, `logging_setup`.
- A single `main()` entry point in `main.py`.
