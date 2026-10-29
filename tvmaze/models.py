"""Data model layer (Module 5): converts TVMaze JSON into Python objects."""

import re
from dataclasses import asdict, dataclass, field

HTML_TAG = re.compile(r"<[^>]+>")

# Genres used by TVMaze (https://www.tvmaze.com/shows).
GENRES = (
    "Action", "Adult", "Adventure", "Anime", "Children", "Comedy", "Crime", "DIY",
    "Drama", "Espionage", "Family", "Fantasy", "Food", "History", "Horror", "Legal",
    "Medical", "Music", "Mystery", "Nature", "Romance", "Science-Fiction", "Sports",
    "Supernatural", "Thriller", "Travel", "War", "Western",
)  # fmt: skip


def normalise_genre(value: str) -> str:
    """Return the TVMaze spelling of a genre, e.g. "comedy" -> "Comedy".

    Raises ValueError if the value is not a known genre.
    """
    for genre in GENRES:
        if genre.lower() == value.strip().lower():
            return genre
    raise ValueError(f"Unknown genre '{value}'. Choose from: {', '.join(GENRES)}")


@dataclass
class Show:
    """A TV show as returned by the TVMaze API."""

    name: str
    genres: list[str] = field(default_factory=list)
    rating: float | None = None
    # Extra details used by the web UI.
    premiered: str | None = None
    status: str | None = None
    network: str | None = None
    image: str | None = None
    summary: str | None = None
    url: str | None = None
    id: int | None = None

    @classmethod
    def from_api(cls, show_json: dict) -> "Show":
        """Build a Show from a TVMaze "show" object."""
        channel = show_json.get("network") or show_json.get("webChannel") or {}
        image = show_json.get("image") or {}
        summary = show_json.get("summary")
        return cls(
            name=show_json.get("name", "Unknown"),
            genres=show_json.get("genres") or [],
            rating=(show_json.get("rating") or {}).get("average"),
            premiered=show_json.get("premiered"),
            status=show_json.get("status"),
            network=channel.get("name"),
            image=image.get("medium"),
            # The API returns HTML in the summary; keep plain text only.
            summary=HTML_TAG.sub("", summary).strip() if summary else None,
            url=show_json.get("url"),
            id=show_json.get("id"),
        )

    @property
    def genre_text(self) -> str:
        return ", ".join(self.genres) or "N/A"

    @property
    def rating_text(self) -> str:
        return "N/A" if self.rating is None else str(self.rating)

    def to_dict(self) -> dict:
        return asdict(self)
