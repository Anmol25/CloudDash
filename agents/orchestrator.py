from typing import TypedDict, Literal, Annotated
import operator

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage


class Tasks(TypedDict):
    intent: Literal["technical", "billing"]
    task: str
    status: Literal["pending", "completed"]
    entities: list[str]


class AgentResponse(TypedDict):
    response: str
    metadata: dict


class AgentOutput(TypedDict):
    agent: Literal["billing", "technical", "escalation"]
    agent_outputs: list[AgentResponse]


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    tasks: Annotated[list[Tasks], operator.add]
    agent_outputs: list[AgentResponse]
