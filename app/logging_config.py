"""Central logging configuration for the API service."""

import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure root logger with a stream handler.

    Note: auth events are logged at INFO including credential details —
    acceptable for local demos but not production (see auth/service.py).
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(handler)
    root.setLevel(level)
