import logging
from config.schema import AgentState
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "agents.yaml"
with open(_CONFIG_PATH, "r") as f:
    _agents_config = yaml.safe_load(f) or {}

_orchestration_config = _agents_config.get("orchestration", {})
_intent_to_agent = _orchestration_config.get(
    "intents",
    {
        "billing": "billingAgent",
        "technical": "technicalAgent",
        "escalation": "escalationAgent",
    },
)
_fallback_node = _orchestration_config.get("fallback", "finalizer")


def dispatcher_node(state: AgentState):
    return state


dispatch_map = {node: node for node in set(
    _intent_to_agent.values()) | {_fallback_node}}


def dispatcher(state: AgentState):
    """Dispatcher node that routes tasks to the appropriate agent based on the intent identified by the triage agent."""
    try:
        tasks = state["tasks"]
        pending_tasks = [t for t in tasks if t["status"] == "pending"]

        if not pending_tasks:
            return _fallback_node

        next_task = pending_tasks[0]

        intent = next_task["intent"]
        agent_name = _intent_to_agent.get(intent)
        if not agent_name:
            logger.warning("Unknown intent '%s', routing to fallback", intent)
            return _fallback_node
        return agent_name
    except Exception:
        logger.exception("Dispatcher failed, routing to fallback")
        return _fallback_node
