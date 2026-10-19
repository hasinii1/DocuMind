import logging
import sys
import json
from datetime import datetime, timezone

def setup_logger(name: str = "documind") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = setup_logger()

def log_audit_event(event_type: str, details: dict, user_id: str = "anonymous", workspace_id: str = "default"):
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "workspace_id": workspace_id,
        "details": details
    }
    logger.info(f"AUDIT_EVENT: {json.dumps(event)}")
