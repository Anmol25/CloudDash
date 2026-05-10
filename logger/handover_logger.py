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


def _clip_text(text: str | None, limit: int = MAX_TEXT_LEN) -> str | None:
    if text is None:
        return None
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)] + "..."


def _get_last_message_summary(state: AgentState) -> str | None:
    messages = state.get("messages", [])
    if not messages:
        return None
    last_message = messages[-1]
    content = getattr(last_message, "content", None)
    if content is None:
        return None
    if isinstance(content, list):
        content = " ".join(str(item) for item in content)
    return _clip_text(str(content))


def _get_focus_task(state: AgentState) -> Dict[str, Any] | None:
    tasks = state.get("tasks", [])
    if not tasks:
        return None
    pending_tasks = [task for task in tasks if task.get("status") == "pending"]
    task = pending_tasks[0] if pending_tasks else tasks[-1]
    return {
        "intent": task.get("intent"),
        "task": _clip_text(task.get("task")),
        "summary": _clip_text(task.get("summary")),
        "status": task.get("status"),
    }


def build_context_snapshot(state: AgentState) -> Dict[str, Any]:
    return {
        "focus_task": _get_focus_task(state),
        "last_message": _get_last_message_summary(state),
    }


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
