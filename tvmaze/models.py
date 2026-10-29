"""Data model layer (Module 5): converts TVMaze JSON into Python objects."""

import re
from dataclasses import asdict, dataclass, field

HTML_TAG = re.compile(r"<[^>]+>")


@dataclass
class Show:
    """A TV show as returned by the TVMaze API."""

    name: str
    genres: list = field(default_factory=list)
    rating: float | None = None
    # Extra details used by the web UI.
    premiered: str | None = None
    status: str | None = None
    network: str | None = None
    image: str | None = None
    summary: str | None = None
    url: str | None = None

    @classmethod
    def from_api(cls, show_json):
        """Build a Show from the "show" object in a TVMaze search result."""
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
        )

    @property
    def genre_text(self):
        return ", ".join(self.genres) or "N/A"

    @property
    def rating_text(self):
        return "N/A" if self.rating is None else str(self.rating)

    def to_dict(self):
        return asdict(self)
