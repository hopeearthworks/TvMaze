"""TVMaze automation: entry point.

By default this starts the web UI on http://localhost:8080 and opens it in
the browser. With --cli it runs the original command-line automation:
reads config.json, searches the TVMaze API, displays the shows that meet
the rating threshold and saves them to a report file. Activity and errors
are logged to automation.log.

Usage:
    python main.py                        # web UI on http://localhost:8080
    python main.py --port 9000            # web UI on another port
    python main.py --no-browser           # don't open the browser automatically
    python main.py --cli                  # command-line run using config.json
    python main.py --cli --config other.json
"""

import argparse
import logging
import sys
import threading
import webbrowser
from pathlib import Path

import requests

from tvmaze import automation, ui
from tvmaze.config import ConfigError, load_config
from tvmaze.logging_setup import setup_logging
from tvmaze.report import save_report
from tvmaze.web_server import run_server

BASE_DIR = Path(__file__).parent
DEFAULT_CONFIG = BASE_DIR / "config.json"
LOG_FILE = BASE_DIR / "automation.log"
DEFAULT_PORT = 8080

logger = logging.getLogger("tvmaze.main")


def run_cli(config_path):
    """Run the command-line automation and return an exit code."""
    logger.info("Automation started")
    try:
        config = load_config(config_path)
        ui.display_welcome()
        shows, matching_shows = automation.run(config)
        ui.display_shows(matching_shows, len(shows))
        ui.display_summary(config.search_term, config.minimum_rating,
                           len(shows), matching_shows)
        save_report(matching_shows, config.search_term, config.minimum_rating,
                    config.output_file)
        print(f"\nReport saved to {config.output_file}")
    except ConfigError as error:
        logger.error(error)
        return 1
    except requests.RequestException as error:
        logger.error("Unable to retrieve TV show data: %s", error)
        return 1
    except OSError as error:
        logger.error("Unable to create report file: %s", error)
        return 1
    except Exception:
        logger.exception("Unexpected error")
        return 1

    logger.info("Automation finished successfully")
    return 0


def run_web(config_path, port, open_browser):
    """Start the web UI and block until Ctrl+C."""
    url = f"http://localhost:{port}"
    if open_browser:
        # Give the server a moment to start before opening the page.
        threading.Timer(1.0, webbrowser.open, args=[url]).start()
    try:
        run_server(config_path, host="localhost", port=port)
    except OSError as error:
        logger.error("Unable to start the web server on port %d: %s", port, error)
        return 1
    return 0


def parse_args():
    parser = argparse.ArgumentParser(description="TVMaze Show Finder")
    parser.add_argument("--cli", action="store_true",
                        help="run the command-line automation instead of the web UI")
    parser.add_argument("--config", default=DEFAULT_CONFIG,
                        help="path to the configuration file (default: config.json)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"web UI port (default: {DEFAULT_PORT})")
    parser.add_argument("--no-browser", action="store_true",
                        help="don't open the web UI in a browser")
    return parser.parse_args()


def main():
    args = parse_args()
    setup_logging(LOG_FILE)
    if args.cli:
        return run_cli(args.config)
    return run_web(args.config, args.port, not args.no_browser)


if __name__ == "__main__":
    sys.exit(main())
