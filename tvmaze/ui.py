"""Presentation layer (Modules 3 and 4): everything printed to the user."""

NAME_WIDTH = 35
GENRE_WIDTH = 30


def display_welcome():
    """Print a welcome banner."""
    print("=" * 73)
    print(" Welcome to the TVMaze Show Finder")
    print("=" * 73)


def display_shows(shows, total_found):
    """Print the name, genres and rating of each show as a table."""
    if total_found == 0:
        print("No results were returned for this search term.")
        return
    if not shows:
        print("No shows met the minimum rating.")
        return
    print(f"{'Show name':<{NAME_WIDTH}} {'Genre':<{GENRE_WIDTH}} {'Rating':>6}")
    print("-" * 73)
    for show in shows:
        name = show.name[: NAME_WIDTH - 1]
        genres = show.genre_text[: GENRE_WIDTH - 1]
        print(f"{name:<{NAME_WIDTH}} {genres:<{GENRE_WIDTH}} {show.rating_text:>6}")


def display_summary(search_term, minimum_rating, total_found, matching_shows, search_mode="name"):
    """Print a short summary of the run."""
    print()
    print("Summary")
    print("-" * 73)
    print(f"Search {'genre' if search_mode == 'genre' else 'term':<10}: {search_term}")
    print(f"Minimum rating   : {minimum_rating}")
    print(f"Shows found      : {total_found}")
    print(f"Meet threshold   : {len(matching_shows)}")
    if matching_shows:
        average = sum(show.rating for show in matching_shows) / len(matching_shows)
        print(f"Average rating   : {average:.1f}")
