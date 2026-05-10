import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

from config.schema import AgentState

ENV_LOG_PATH = "HANDOVER_LOG_PATH"
DEFAULT_LOG_FILENAME = "logs/handovers.json"
MAX_TEXT_LEN = 500


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_log_path() -> str:
    env_path = os.getenv(ENV_LOG_PATH)
    if env_path:
        return env_path
    return os.path.join(os.path.dirname(__file__), DEFAULT_LOG_FILENAME)


def log_handover(event: Dict[str, Any]) -> None:
    log_path = _resolve_log_path()
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    if "timestamp" not in event:
        event = {**event, "timestamp": _utc_timestamp()}
    with open(log_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=True) + "\n")
