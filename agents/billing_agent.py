import json

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from orchestrator import AgentState, Tasks
from langchain_core.messages import SystemMessage
from retrieval.retriever import retriever_tool
from orchestrator import AgentResponse, AgentOutput

with open("../config/agent_prompts.json", "r") as f:
    prompts = json.load(f)
    BILLING_AGENT = prompts["BILLING_AGENT"]


def billingAgent(state: AgentState) -> AgentState:
    tasks = state["tasks"]

    current_task = next(
        t for t in tasks
        if t["intent"] == "billing"
        and t["status"] == "pending"
    )

    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    model_with_tool = model.bind_tools([retriever_tool])
    structured_response = model_with_tool.with_structured_output(AgentResponse)

    response = structured_response.invoke(
        [SystemMessage(content=BILLING_AGENT),
         *state["messages"]]
    )
    current_task["status"] = "completed"
    return {
        "tasks": tasks,
        "agent_outputs": state["agent_outputs"] + [AgentOutput(agent="billing", response=response.response, metadata=response.metadata)]
    }
