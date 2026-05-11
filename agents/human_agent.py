import logging
import yaml

from langchain_google_genai import ChatGoogleGenerativeAI
from config.schema import AgentState
from langchain_core.messages import SystemMessage

logger = logging.getLogger(__name__)
with open("./config/agents.yaml", "r") as f:
    agents_config = yaml.safe_load(f)

humanAgent_config = agents_config["human_agent"]
prompt_location = "./config/" + humanAgent_config["system_prompt"]
with open(prompt_location, "r") as f:
    SYSTEM_PROMPT = f.read()


def humanAgent(state: AgentState) -> AgentState:
    """
    Agent responsible for simulating human interaction. 
    It takes tasks that require human intervention (e.g., escalation) 
    and generates responses as if a human were handling them. This agent
    can be used to simulate customer support interactions or to provide 
    fallback responses when other agents fail.
    """
    escalation_outputs = state["escalation_outputs"]

    current_task = next(
        t for t in escalation_outputs
        if t["status"] == "pending"
    )

    try:
        model = ChatGoogleGenerativeAI(
            model=humanAgent_config["model"], temperature=humanAgent_config["temperature"])
        response = model.invoke(
            [SystemMessage(content=SYSTEM_PROMPT),
             *state["messages"], SystemMessage(content=f"Your task:\nintent: {current_task['intent']}\n\n task: {current_task['task']}\n\nsummary: {current_task['context_summary']}\n\nurgency: {current_task['urgency']}\n\nsentiment: {current_task['sentiment']}")]
        )
        return {"messages": [response]}
    except Exception:
        logger.exception("Human agent failed")
        fallback = "Human agent failed. Please route this request to a live operator."
        return {"messages": [SystemMessage(content=fallback)]}
