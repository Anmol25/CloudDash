import yaml

from langchain_google_genai import ChatGoogleGenerativeAI
from config.schema import AgentState
from langchain_core.messages import SystemMessage

with open("./config/agents.yaml", "r") as f:
    agents_config = yaml.safe_load(f)

humanAgent_config = agents_config["human_agent"]
prompt_location = "./config/" + humanAgent_config["system_prompt"]
with open(prompt_location, "r") as f:
    SYSTEM_PROMPT = f.read()


def humanAgent(state: AgentState) -> AgentState:
    escalation_outputs = state["escalation_outputs"]

    current_task = next(
        t for t in escalation_outputs
        if t["status"] == "pending"
    )

    model = ChatGoogleGenerativeAI(
        model=humanAgent_config["model"], temperature=humanAgent_config["temperature"])
    response = model.invoke(
        [SystemMessage(content=SYSTEM_PROMPT),
         *state["messages"], SystemMessage(content=f"Your task:\nintent: {current_task['intent']}\n\n task: {current_task['task']}\n\nsummary: {current_task['context_summary']}\n\nurgency: {current_task['urgency']}\n\nsentiment: {current_task['sentiment']}")]
    )
    return {"messages": [response]}
