"""Logging setup for the Vedaws runtime."""

from __future__ import annotations

import logging
from pathlib import Path

from vedaws.config.schema import LoggingConfig


def setup_logging(config: LoggingConfig) -> logging.Logger:
    level_name = (config.level or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    root = logging.getLogger("vedaws")
    root.handlers.clear()
    root.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    if config.file:
        log_path = Path(config.file).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    root.debug("Logging initialized at level %s", config.level)
    return root
