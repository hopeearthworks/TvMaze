# Module 3: Generating the First Automation Script: Prompts Used

The first version of the project was one script that asked for a search term, showed a welcome message, simulated retrieving data and displayed a summary. Its welcome and summary functions became the presentation layer, `tvmaze/ui.py`. The simulated data was replaced by the real API in Module 5, and the typed search term was replaced by `config.json` in Module 6.

## Prompt 1: Generate (too vague)
> Write a Python script that searches for something.

**Result:** generic code with no welcome message, no simulated data and no summary. The prompt didn't say what was needed.

## Prompt 2: Generate (improved)
> Write a Python 3 script that:
> 1. Displays a welcome message.
> 2. Asks the user for a search term.
> 3. Simulates retrieving data by filtering a hard-coded list of TV shows (name, genre, rating), with a short delay to imitate a network call.
> 4. Displays the matching results and a summary with the number of matches and the average rating.
> Use small functions with docstrings and a `main()` function with an `if __name__ == "__main__":` guard.

**Result:** a structured script close to what was needed.

## Prompt 2b: Improve (course example)
> Improve the previous script by: adding functions, using clear variable names, displaying a more professional summary, adding comments explaining the code, and handling empty user input.

## Prompt 3: Explain
> Explain this script line by line for a beginner. What does `if __name__ == "__main__":` do, and why filter the data with a list comprehension?

## Prompt 4: Improve the code
> Improve this script: reject empty search terms, make the search case-insensitive, and handle "no results" without dividing by zero.

**Changes:** input validation, `.lower()` comparisons, a guard on the average calculation (still present in `ui.display_summary`).

## Prompt 5: Prepare for the next layer
> Split the display code into its own module so the data source can later be swapped for a real API.

**Result:** `tvmaze/ui.py` (`display_welcome`, `display_shows`, `display_summary`).

## Original Module 3 version (for reference)
```python
import time

SAMPLE_SHOWS = [
    {"name": "Doctor Who", "genre": "Science-Fiction", "rating": 7.9},
    {"name": "Sherlock", "genre": "Crime", "rating": 8.8},
    {"name": "Luther", "genre": "Crime", "rating": 8.4},
]

def display_welcome():
    print("=" * 40)
    print(" Welcome to the TV Show Search Tool")
    print("=" * 40)

def get_search_term():
    while True:
        term = input("Enter a search term: ").strip()
        if term:
            return term
        print("Search term cannot be empty. Please try again.")

def retrieve_data(search_term):
    print(f"\nSearching for '{search_term}'...")
    time.sleep(1)  # Simulate network delay.
    term = search_term.lower()
    return [s for s in SAMPLE_SHOWS
            if term in s["name"].lower() or term in s["genre"].lower()]

def display_summary(search_term, results):
    for show in results:
        print(f"  - {show['name']} ({show['genre']}) rated {show['rating']}")
    print(f"Search term : {search_term}")
    print(f"Matches     : {len(results)}")
    if results:
        print(f"Avg rating  : {sum(s['rating'] for s in results) / len(results):.1f}")

def main():
    display_welcome()
    term = get_search_term()
    display_summary(term, retrieve_data(term))

if __name__ == "__main__":
    main()
```

Sample run (search "crime"): matched Sherlock and Luther, with an average rating of 8.6.

## Lessons learned
- Specific prompts (inputs, steps, outputs, structure) produce much better code.
- Ask the AI to explain its code before you trust it.
- Make improvements in small steps, testing after each one.
