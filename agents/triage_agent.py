import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
import yaml
from config.schema import AgentState, Tasks
from langchain_core.messages import SystemMessage

logger = logging.getLogger(__name__)

with open("./config/agents.yaml", "r") as f:
    agents_config = yaml.safe_load(f)

triageAgent_config = agents_config["triage_agent"]
prompt_location = "./config/" + triageAgent_config["system_prompt"]
with open(prompt_location, "r") as f:
    SYSTEM_PROMPT = f.read()


class TriageAgentResponse(BaseModel):
    """Response from the triage agent containing a list of tasks with their intent, task description, priority, and associated entities."""
    tasks: list[Tasks]


def triageAgent(state: AgentState) -> AgentState:
    """
    Agent responsible for triaging incoming tasks.
    It analyzes the input messages and identifies tasks, 
    classifying them by intent (e.g., technical, billing, escalation), 
    assigning a priority level, and extracting relevant entities. 
    The output is a structured list of tasks that can be further processed by specialized agents.
    """
    try:
        model = ChatGoogleGenerativeAI(
            model=triageAgent_config["model"], temperature=triageAgent_config["temperature"])
        structured_response = model.with_structured_output(TriageAgentResponse)
        response = structured_response.invoke(
            [SystemMessage(content=SYSTEM_PROMPT),
             *state["messages"]]
        )
        return {"tasks": response.tasks}
    except Exception:
        logger.exception("Triage agent failed")
        last_message = state["messages"][-1].content if state.get(
            "messages") else ""
        fallback_task = {
            "intent": "escalation",
            "task": "Triage failed. Please review the user request manually.",
            "summary": last_message,
            "status": "pending",
            "entities": [],
        }
        return {"tasks": [fallback_task]}
