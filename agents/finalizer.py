import yaml

from config.schema import AgentState
from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

with open("./config/agents.yaml", "r") as f:
    agents_config = yaml.safe_load(f)

finalizerAgent_config = agents_config["finalizer_agent"]
prompt_location = "./config/" + finalizerAgent_config["system_prompt"]
with open(prompt_location, "r") as f:
    SYSTEM_PROMPT = f.read()


def finalizer(state: AgentState) -> AgentState:
    outputs = state["agent_outputs"]
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    final_response = model.invoke(
        [SystemMessage(content=SYSTEM_PROMPT),
         *state["messages"],
         *[SystemMessage(content=f"Agent: {output['agent'].capitalize()}\n Agent Task: {output['task']}\n Agent Response: {output['response']}") for output in outputs]]
    )
    return {"messages": [final_response]}
