"""Web layer: serves the Bootstrap UI and a small JSON API.

Endpoints:
    GET /                -> web/index.html (plus /css, /js static files)
    GET /api/config      -> default search term and rating from config.json
    GET /api/search?q=<term>&min_rating=<0-10>
                         -> shows found, with a flag for those meeting the rating
"""

import json
import logging
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

from tvmaze import automation
from tvmaze.api_client import search_shows
from tvmaze.config import ConfigError, load_config

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

logger = logging.getLogger(__name__)


def parse_minimum_rating(value):
    """Convert the min_rating query value to a float between 0 and 10."""
    try:
        rating = float(value)
    except (TypeError, ValueError):
        raise ValueError("Minimum rating must be a number")
    if not 0 <= rating <= 10:
        raise ValueError("Minimum rating must be between 0 and 10")
    return rating


def build_search_response(search_term, minimum_rating):
    """Run the automation and shape the result for the UI."""
    shows = search_shows(search_term)
    matching = automation.filter_by_rating(shows, minimum_rating)
    average = (sum(show.rating for show in matching) / len(matching)) if matching else None
    return {
        "search_term": search_term.strip(),
        "minimum_rating": minimum_rating,
        "total_found": len(shows),
        "matching_count": len(matching),
        "average_rating": round(average, 1) if average is not None else None,
        "shows": [dict(show.to_dict(), meets_threshold=show in matching) for show in shows],
    }


class RequestHandler(BaseHTTPRequestHandler):
    config_path = None  # Set by run_server.

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/api/config":
            self.handle_config()
        elif url.path == "/api/search":
            self.handle_search(parse_qs(url.query))
        else:
            self.serve_static(url.path)

    def handle_config(self):
        try:
            config = load_config(self.config_path)
        except ConfigError as error:
            logger.error(error)
            self.send_json({"search_term": "", "minimum_rating": 0})
            return
        self.send_json({"search_term": config.search_term,
                        "minimum_rating": config.minimum_rating})

    def handle_search(self, query):
        search_term = query.get("q", [""])[0]
        try:
            minimum_rating = parse_minimum_rating(query.get("min_rating", ["0"])[0])
            self.send_json(build_search_response(search_term, minimum_rating))
        except ValueError as error:
            logger.error("Invalid search request: %s", error)
            self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
        except requests.RequestException as error:
            logger.error("Unable to retrieve TV show data: %s", error)
            self.send_json({"error": "Unable to reach the TVMaze service. Please try again."},
                           HTTPStatus.BAD_GATEWAY)
        except Exception:
            logger.exception("Unexpected error during search")
            self.send_json({"error": "Unexpected server error."},
                           HTTPStatus.INTERNAL_SERVER_ERROR)

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
        self.send_bytes(json.dumps(payload).encode("utf-8"),
                        "application/json; charset=utf-8", status)

    def send_bytes(self, body, content_type, status=HTTPStatus.OK):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
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
