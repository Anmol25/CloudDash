import logging
import yaml

from langchain_google_genai import ChatGoogleGenerativeAI
from config.schema import AgentState
from langchain_core.messages import SystemMessage
from config.schema import EscalationAgentOutput

logger = logging.getLogger(__name__)

with open("./config/agents.yaml", "r") as f:
    agents_config = yaml.safe_load(f)

escalationAgent_config = agents_config["escalation_agent"]
prompt_location = "./config/" + escalationAgent_config["system_prompt"]
with open(prompt_location, "r") as f:
    SYSTEM_PROMPT = f.read()


def escalationAgent(state: AgentState) -> AgentState:
    """
    Agent responsible for handling escalation tasks. 
    When a task is marked for escalation, this agent processes the task details and packages content for human operators to review. 
    It ensures that all relevant information about the task is included in the escalation output, making it easier for human operators 
    to understand and address the issue effectively.
    """
    tasks = state["tasks"]
    escalations_outputs = state["escalation_outputs"]

    current_task = next(
        t for t in tasks
        if t["intent"] == "escalation"
        and t["status"] == "pending"
    )

    try:
        model = ChatGoogleGenerativeAI(
            model=escalationAgent_config["model"], temperature=escalationAgent_config["temperature"])
        structured_response = model.with_structured_output(
            EscalationAgentOutput)

        response = structured_response.invoke(
            [SystemMessage(content=SYSTEM_PROMPT),
             *state["messages"], SystemMessage(content=f"Your task:\n\n task: {current_task['task']}\n\nsummary: {current_task['summary']}\n\nentities: {', '.join(current_task['entities'])}")]
        )

        current_task["status"] = "completed"
        return {"tasks": tasks, "escalation_outputs": escalations_outputs + [response]}
    except Exception:
        logger.exception("Escalation agent failed")
        current_task["status"] = "failed"
        fallback = {
            "agent": "escalation",
            "intent": current_task["intent"],
            "task": current_task["task"],
            "context_summary": current_task["summary"],
            "urgency": "medium",
            "sentiment": "neutral",
            "status": "pending",
            "task_status": "failed",
            "response": "Escalation agent failed. Please review this request manually.",
        }
        return {"tasks": tasks, "escalation_outputs": escalations_outputs + [fallback]}
