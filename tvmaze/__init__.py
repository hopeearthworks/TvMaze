"""TVMaze automation package.

Layers, added module by module:
    ui.py          - Module 3/4: presentation (welcome, results, summary)
    models.py      - Module 5: JSON -> Python objects (Show)
    api_client.py  - Module 5: TVMaze API access
    config.py      - Module 6: external configuration (config.json)
    automation.py  - Module 6: business logic (rating filter, run)
    report.py      - Module 7/8: saves matching shows to a report file
    logging_setup.py - Module 8: file and error logging
    web_server.py  - Extension: JSON API + static files for the Bootstrap UI
"""
