from typing import TypedDict, Literal, Annotated
import operator

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class Tasks(TypedDict):
    intent: Literal["technical", "billing", "escalation"]
    task: str
    summary: str
    status: Literal["pending", "completed"]
    entities: list[str]


class AgentOutput(TypedDict):
    agent: Literal["billing", "technical", "escalation"]
    task: str
    response: str


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    tasks: list[Tasks]
    agent_outputs: list[AgentOutput]
