"""Web layer: serves the Bootstrap UI and a small JSON API.

Endpoints:
    GET /                -> web/index.html (plus /css, /js static files)
    GET /api/config      -> default search term, mode and rating from config.json,
                            plus the list of genres
    GET /api/search?q=<term>&min_rating=<0-10>&mode=<name|genre>
                         -> shows found, with a flag for those meeting the rating
    GET /api/report?<same as search>&format=<txt|csv>
                         -> the matching shows as a downloadable report
    GET /api/show?id=<TVMaze show ID>
                         -> cast and next episode for the details modal
"""

import json
import logging
import mimetypes
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

from tvmaze import automation
from tvmaze.api_client import get_show_details
from tvmaze.config import SEARCH_MODES, ConfigError, load_config
from tvmaze.models import GENRES
from tvmaze.report import format_report_csv, format_report_text

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

logger = logging.getLogger(__name__)


def parse_search_mode(value):
    """Validate the mode query value ("name" or "genre")."""
    mode = (value or "name").strip().lower()
    if mode not in SEARCH_MODES:
        raise ValueError(f"Search mode must be one of: {', '.join(SEARCH_MODES)}")
    return mode


def parse_minimum_rating(value):
    """Convert the min_rating query value to a float between 0 and 10."""
    try:
        rating = float(value)
    except (TypeError, ValueError):
        raise ValueError("Minimum rating must be a number") from None
    if not 0 <= rating <= 10:
        raise ValueError("Minimum rating must be between 0 and 10")
    return rating


def parse_show_id(query):
    """Return the positive integer show ID from the query string."""
    value = query.get("id", [""])[0]
    if not value.isdigit() or int(value) <= 0:
        raise ValueError("Show ID must be a positive whole number")
    return int(value)


def parse_search_query(query):
    """Return (search_term, minimum_rating, search_mode) from the query string."""
    search_term = query.get("q", [""])[0]
    minimum_rating = parse_minimum_rating(query.get("min_rating", ["0"])[0])
    search_mode = parse_search_mode(query.get("mode", ["name"])[0])
    return search_term, minimum_rating, search_mode


def build_search_response(search_term, minimum_rating, search_mode="name"):
    """Run the automation and shape the result for the UI."""
    shows = automation.search(search_term, search_mode)
    matching = automation.filter_by_rating(shows, minimum_rating)
    average = (sum(show.rating or 0 for show in matching) / len(matching)) if matching else None
    return {
        "search_term": search_term.strip(),
        "search_mode": search_mode,
        "minimum_rating": minimum_rating,
        "total_found": len(shows),
        "matching_count": len(matching),
        "average_rating": round(average, 1) if average is not None else None,
        "shows": [
            dict(show.to_dict(), meets_threshold=automation.meets_threshold(show, minimum_rating))
            for show in shows
        ],
    }


class RequestHandler(BaseHTTPRequestHandler):
    config_path: Path | str = Path("config.json")  # Set by run_server.

    def do_GET(self):
        url = urlparse(self.path)
        query = parse_qs(url.query)
        if url.path == "/api/config":
            self.handle_config()
        elif url.path == "/api/search":
            self.handle_api(
                lambda: self.send_json(build_search_response(*parse_search_query(query)))
            )
        elif url.path == "/api/report":
            self.handle_api(lambda: self.handle_report(query))
        elif url.path == "/api/show":
            self.handle_api(lambda: self.send_json(get_show_details(parse_show_id(query))))
        else:
            self.serve_static(url.path)

    def handle_config(self):
        defaults = {"search_term": "", "search_mode": "name", "minimum_rating": 0}
        try:
            config = load_config(self.config_path)
            defaults = {
                "search_term": config.search_term,
                "search_mode": config.search_mode,
                "minimum_rating": config.minimum_rating,
            }
        except ConfigError as error:
            logger.error(error)
        self.send_json({**defaults, "genres": list(GENRES)})

    def handle_report(self, query):
        """Send the matching shows as a downloadable .txt or .csv report."""
        search_term, minimum_rating, search_mode = parse_search_query(query)
        report_format = query.get("format", ["txt"])[0].lower()
        if report_format not in ("txt", "csv"):
            raise ValueError("Report format must be 'txt' or 'csv'")

        matching = automation.filter_by_rating(
            automation.search(search_term, search_mode), minimum_rating
        )
        if report_format == "csv":
            body, content_type = format_report_csv(matching), "text/csv; charset=utf-8"
        else:
            body = format_report_text(matching, search_term.strip(), minimum_rating)
            content_type = "text/plain; charset=utf-8"
        safe_name = re.sub(r"[^A-Za-z0-9-]+", "_", search_term.strip()).strip("_") or "shows"
        filename = f"tv_report_{safe_name}.{report_format}"
        logger.info("Report download: %s (%d show(s))", filename, len(matching))
        self.send_bytes(
            body.encode("utf-8"),
            content_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    def handle_api(self, action):
        """Run an API action, turning errors into JSON error responses."""
        try:
            action()
        except ValueError as error:
            logger.error("Invalid request: %s", error)
            self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
        except requests.HTTPError as error:
            if error.response is not None and error.response.status_code == 404:
                logger.warning("TVMaze has no record for %s", self.path)
                self.send_json({"error": "Show not found."}, HTTPStatus.NOT_FOUND)
                return
            logger.error("Unable to retrieve TV show data: %s", error)
            self.send_json(
                {"error": "Unable to reach the TVMaze service. Please try again."},
                HTTPStatus.BAD_GATEWAY,
            )
        except requests.RequestException as error:
            logger.error("Unable to retrieve TV show data: %s", error)
            self.send_json(
                {"error": "Unable to reach the TVMaze service. Please try again."},
                HTTPStatus.BAD_GATEWAY,
            )
        except Exception:
            logger.exception("Unexpected error handling %s", self.path)
            self.send_json({"error": "Unexpected server error."}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def serve_static(self, path):
        relative = "index.html" if path in ("", "/") else path.lstrip("/")
        file_path = (WEB_DIR / relative).resolve()
        # Refuse anything outside the web folder (e.g. "/../config.json").
        if not file_path.is_file() or not file_path.is_relative_to(WEB_DIR):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        self.send_bytes(file_path.read_bytes(), content_type)

    def send_json(self, payload, status=HTTPStatus.OK):
        self.send_bytes(
            json.dumps(payload).encode("utf-8"), "application/json; charset=utf-8", status
        )

    def send_bytes(self, body, content_type, status=HTTPStatus.OK, headers=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        logger.info("%s - %s", self.address_string(), format % args)


def run_server(config_path, host="localhost", port=8080):
    """Start the web server and block until interrupted."""
    RequestHandler.config_path = config_path
    server = ThreadingHTTPServer((host, port), RequestHandler)
    logger.info("Web UI started on http://%s:%d", host, port)
    print(f"TVMaze Show Finder running at http://{host}:{port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        logger.info("Web UI stopped")
