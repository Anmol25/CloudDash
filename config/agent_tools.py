import importlib
from pathlib import Path
import yaml

_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "agents.yaml"


def load_agents_config():
    with open(_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f) or {}


def _import_handler(module_path, handler_name):
    module = importlib.import_module(module_path)
    handler = getattr(module, handler_name, None)
    if not handler:
        raise ImportError(
            f"Handler '{handler_name}' not found in {module_path}")
    return handler


def resolve_tool_spec(tool_spec, tool_registry):
    if isinstance(tool_spec, dict):
        module_path = tool_spec.get("module")
        handler_name = tool_spec.get("handler")
        if not module_path or not handler_name:
            raise ValueError("Tool spec must include 'module' and 'handler'.")
        return _import_handler(module_path, handler_name)

    if isinstance(tool_spec, str):
        tool = tool_registry.get(tool_spec)
        if not tool:
            raise ValueError(f"Unknown tool: {tool_spec}")
        return tool

    raise ValueError("Tool spec must be a string or a dict.")


def build_tool_registry(config=None):
    registry = {}
    config = config or load_agents_config()
    tool_defs = config.get("tools", {})
    if isinstance(tool_defs, dict):
        for tool_name, tool_spec in tool_defs.items():
            registry[tool_name] = resolve_tool_spec(tool_spec, registry)
    return registry


def build_tool_list(tool_specs, tool_registry):
    return [resolve_tool_spec(tool_spec, tool_registry) for tool_spec in tool_specs]


def get_agent_tools(agent_key, config=None, tool_registry=None):
    config = config or load_agents_config()
    tool_registry = tool_registry or build_tool_registry(config)
    agent_config = config.get(agent_key, {})
    tool_specs = agent_config.get("tools", [])
    return build_tool_list(tool_specs, tool_registry)
