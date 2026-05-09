from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
import yaml
from config.schema import AgentState, Tasks
from langchain_core.messages import SystemMessage


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
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    structured_response = model.with_structured_output(TriageAgentResponse)
    response = structured_response.invoke(
        [SystemMessage(content=SYSTEM_PROMPT),
         *state["messages"]]
    )
    return {"tasks": response.tasks}
