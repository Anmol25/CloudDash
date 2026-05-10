import json

from handover.handover_logger import build_context_snapshot, log_handover

from langgraph.graph import StateGraph, START, END
from config.schema import AgentState
from .technical_agent import technicalAgent
from .billing_agent import billingAgent
from .dispatcher import dispatcher, dispatcher_node, dispatch_map
from .finalizer import finalizer
from .triage_agent import triageAgent
from .escalation_agent import escalationAgent
from .human_agent import humanAgent
from langgraph.prebuilt import ToolNode, tools_condition
from retrieval.retriever import get_retriever_tool
from langchain_core.messages import HumanMessage


class AgentOrchestrator:
    def __init__(self, collection, thread_id, checkpointer):
        self.collection = collection
        self.thread_id = thread_id
        self.checkpointer = checkpointer
        self.graph = StateGraph(AgentState)
        self.retriever_tool = get_retriever_tool(collection)
        # Tools
        self.billing_tools = ToolNode([self.retriever_tool])
        self.technical_tools = ToolNode([self.retriever_tool])
        # workflow
        self.workflow = self.__create_graph()
        self.agent_nodes = {
            "triageAgent",
            "billingAgent",
            "technicalAgent",
            "escalationAgent",
            "humanAgent",
            "finalizer",
        }

    def __create_graph(self):
        self.graph.add_node("triageAgent", triageAgent)
        self.graph.add_node("billingAgent", billingAgent)
        self.graph.add_node("technicalAgent", technicalAgent)
        self.graph.add_node("billingTools", self.billing_tools)
        self.graph.add_node("technicalTools", self.technical_tools)
        self.graph.add_node("finalizer", finalizer)
        self.graph.add_node("dispatcher", dispatcher_node)
        self.graph.add_node("escalationAgent", escalationAgent)
        self.graph.add_node("humanAgent", humanAgent)

        # START
        self.graph.add_edge(START, "triageAgent")

        # TRIAGE ROUTING
        self.graph.add_conditional_edges(
            "triageAgent",
            dispatcher,
            dispatch_map
        )

        self.graph.add_conditional_edges(
            "dispatcher",
            dispatcher,
            dispatch_map
        )

        # BILLING AGENT
        self.graph.add_conditional_edges(
            "billingAgent",
            tools_condition,
            {
                "tools": "billingTools",
                "__end__": "dispatcher"
            }
        )

        self.graph.add_edge(
            "billingTools",
            "billingAgent"
        )

        # TECHNICAL AGENT
        self.graph.add_conditional_edges(
            "technicalAgent",
            tools_condition,
            {
                "tools": "technicalTools",
                "__end__": "dispatcher"
            }
        )

        self.graph.add_edge(
            "technicalTools",
            "technicalAgent"
        )
        # ESCALATION AND HUMAN AGENT
        self.graph.add_edge("escalationAgent", "humanAgent")
        self.graph.add_edge("humanAgent", END)

        # FINALIZER
        self.graph.add_edge("finalizer", END)

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
            if chunk["type"] == "updates":
                updates = chunk["data"]
                for node_name, state_update in updates.items():
                    if isinstance(state_update, dict):
                        active_state.update(state_update)
                    if node_name in self.agent_nodes:
                        if previous_agent and previous_agent != node_name:
                            reason = self._derive_handover_reason(
                                previous_agent, node_name, active_state)
                            log_handover({
                                "thread_id": self.thread_id,
                                "source_agent": previous_agent,
                                "target_agent": node_name,
                                "reason": reason,
                                "context_snapshot": build_context_snapshot(active_state),
                            })
                        previous_agent = node_name
            if chunk["type"] == "messages":
                msg, metadata = chunk["data"]
                if msg.content and (metadata["langgraph_node"] == "finalizer" or metadata["langgraph_node"] == "humanAgent"):
                    print(msg.content)
                    yield json.dumps({"type": "message", "content": msg.content}).encode('utf-8') + b'\n'

    def _derive_handover_reason(self, source_agent, target_agent, state):
        if target_agent == "escalationAgent":
            return {"code": "escalation", "detail": "Routed to escalation"}
        if target_agent == "humanAgent":
            return {"code": "handoff_to_human", "detail": "Escalation flow"}
        if target_agent == "finalizer":
            return {"code": "completion", "detail": "No pending tasks"}
        if target_agent in {"billingAgent", "technicalAgent"}:
            intent = self._get_next_intent(state)
            detail = f"intent={intent}" if intent else "intent=unknown"
            return {"code": "intent_routing", "detail": detail}
        return {"code": "agent_transition", "detail": f"{source_agent} -> {target_agent}"}

    def _get_next_intent(self, state):
        tasks = state.get("tasks", [])
        for task in tasks:
            if task.get("status") == "pending":
                return task.get("intent")
        return None
