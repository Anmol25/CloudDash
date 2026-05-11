import json
import importlib
from pathlib import Path
import yaml

from logger.handover_logger import log_handover

from langgraph.graph import StateGraph, START, END
from config.schema import AgentState
from .dispatcher import dispatcher, dispatcher_node, dispatch_map
from langgraph.prebuilt import ToolNode, tools_condition
from retrieval.retriever import get_retriever_tool
from langchain_core.messages import HumanMessage
from langchain_core.load import dumps

_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "agents.yaml"
with open(_CONFIG_PATH, "r") as f:
    _agents_config = yaml.safe_load(f) or {}


class AgentOrchestrator:
    def __init__(self, collection, thread_id, checkpointer):
        self.collection = collection
        self.thread_id = thread_id
        self.checkpointer = checkpointer
        self.graph = StateGraph(AgentState)
        self.retriever_tool = get_retriever_tool(collection)
        self.orchestration = self._load_orchestration_config()
        self.tool_registry = {
            "retrieval_tool": self.retriever_tool,
        }
        self.agent_nodes = set(self.orchestration["nodes"].keys())
        self.output_nodes = set(
            self.orchestration.get("output_nodes", ["finalizer", "humanAgent"])
        )
        self.workflow = self._create_graph()

    def _load_orchestration_config(self):
        orchestration = _agents_config.get("orchestration")
        if orchestration:
            return orchestration

    def _import_handler(self, module_path, handler_name):
        module = importlib.import_module(module_path)
        handler = getattr(module, handler_name, None)
        if not handler:
            raise ImportError(
                f"Handler '{handler_name}' not found in {module_path}")
        return handler

    def _create_graph(self):
        nodes = self.orchestration["nodes"]
        entrypoint = self.orchestration.get("entrypoint", "triageAgent")
        router_nodes = set(self.orchestration.get(
            "router_nodes", [entrypoint]))

        self.graph.add_node("dispatcher", dispatcher_node)

        for node_name, node_config in nodes.items():
            handler = self._import_handler(
                node_config["module"], node_config["handler"]
            )
            self.graph.add_node(node_name, handler)

            tools = node_config.get("tools", [])
            after = node_config.get("after", "dispatcher")

            if tools:
                tool_instances = []
                for tool_spec in tools:
                    if isinstance(tool_spec, dict):
                        tool = self._import_handler(
                            tool_spec["module"], tool_spec["handler"]
                        )
                    else:
                        tool = self.tool_registry.get(tool_spec)
                    if not tool:
                        raise ValueError(f"Unknown tool: {tool_spec}")
                    tool_instances.append(tool)

                tool_node_name = f"{node_name}Tools"
                self.graph.add_node(tool_node_name, ToolNode(tool_instances))
                self.graph.add_conditional_edges(
                    node_name,
                    tools_condition,
                    {
                        "tools": tool_node_name,
                        "__end__": after,
                    },
                )
                self.graph.add_edge(tool_node_name, node_name)
            elif node_name in router_nodes:
                self.graph.add_conditional_edges(
                    node_name,
                    dispatcher,
                    dispatch_map,
                )
            else:
                if after == "__end__":
                    self.graph.add_edge(node_name, END)
                else:
                    self.graph.add_edge(node_name, after)

        # START
        self.graph.add_edge(START, entrypoint)

        # DISPATCHER ROUTING
        self.graph.add_conditional_edges(
            "dispatcher",
            dispatcher,
            dispatch_map,
        )

        workflow = self.graph.compile(checkpointer=self.checkpointer)
        return workflow

    def run(self, msg):
        initial_state = {"messages": [HumanMessage(content=msg)], "tasks": [
        ], "agent_outputs": [], "escalation_outputs": []}
        config = {"configurable": {
            "collection": self.collection, "thread_id": self.thread_id}}
        active_state = dict(initial_state)
        previous_agent = None
        # stream thread_id
        yield json.dumps({"type": "thread_id", "thread_id": self.thread_id}).encode('utf-8') + b'\n'
        # stream messages
        for chunk in self.workflow.stream(initial_state, config=config, stream_mode=["messages", "updates"], version="v2"):
            # log handovers
            if chunk["type"] == "updates":
                updates = chunk["data"]
                for node_name, state_update in updates.items():
                    if isinstance(state_update, dict):
                        active_state.update(state_update)
                    if node_name in self.agent_nodes:
                        if previous_agent and previous_agent != node_name:
                            log_handover({
                                "thread_id": self.thread_id,
                                "source_agent": previous_agent,
                                "target_agent": node_name,
                                "context_snapshot": dumps(active_state),
                            })
                        previous_agent = node_name
            if chunk["type"] == "messages":
                msg, metadata = chunk["data"]
                if msg.content and (metadata["langgraph_node"] in self.output_nodes):
                    print(msg.content)
                    yield json.dumps({"type": "message", "content": msg.content}).encode('utf-8') + b'\n'
