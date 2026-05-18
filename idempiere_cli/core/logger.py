from __future__ import annotations

import logging
from pathlib import Path


def get_log_dir() -> Path:
    path = Path.home() / ".idempiere-cli" / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("idempiere-cli")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    log_file = get_log_dir() / "idempiere-cli.log"
    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger
