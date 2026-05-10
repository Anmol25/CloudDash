from typing import TypedDict, Literal, Annotated

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class Tasks(TypedDict):
    intent: str
    task: str
    summary: str
    status: Literal["pending", "completed", "failed"]
    entities: list[str]


class AgentOutput(TypedDict):
    agent: str
    task: str
    task_status: Literal["completed", "failed"]
    response: str


class EscalationAgentOutput(AgentOutput):
    agent: str
    intent: str
    task: str
    context_summary: str
    urgency: Literal["low", "medium", "high"]
    sentiment: Literal["positive", "neutral", "negative"]
    status: Literal["pending", "completed"]


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    tasks: list[Tasks]
    agent_outputs: list[AgentOutput]
    escalation_outputs: list[EscalationAgentOutput]
