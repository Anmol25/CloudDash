from langgraph.graph import StateGraph, START, END
from config.schema import AgentState
from .technical_agent import technicalAgent
from .billing_agent import billingAgent
from .dispatcher import dispatcher, dispatcher_node
from .finalizer import finalizer
from .triage_agent import triageAgent
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

    def __create_graph(self):
        self.graph.add_node("triageAgent", triageAgent)
        self.graph.add_node("billingAgent", billingAgent)
        self.graph.add_node("technicalAgent", technicalAgent)
        self.graph.add_node("billingTools", self.billing_tools)
        self.graph.add_node("technicalTools", self.technical_tools)
        self.graph.add_node("finalizer", finalizer)
        self.graph.add_node("dispatcher", dispatcher_node)

        # START
        self.graph.add_edge(START, "triageAgent")

        # TRIAGE ROUTING
        self.graph.add_conditional_edges(
            "triageAgent",
            dispatcher
        )

        self.graph.add_conditional_edges(
            "dispatcher",
            dispatcher
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

        # FINALIZER
        self.graph.add_edge("finalizer", END)

        workflow = self.graph.compile(checkpointer=self.checkpointer)
        return workflow

    def run(self, msg):
        initial_state = {"messages": [HumanMessage(content=msg)], "tasks": [
        ], "agent_outputs": []}
        config = {"collection": self.collection, "thread_id": self.thread_id}
        final_state = self.workflow.invoke(
            initial_state, config=config)
        print("Final State:", final_state)
        return final_state
