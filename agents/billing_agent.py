import yaml

from langchain_google_genai import ChatGoogleGenerativeAI
from config.schema import AgentState
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from retrieval.retriever import get_retriever_tool
from config.schema import AgentOutput

with open("./config/agents.yaml", "r") as f:
    agents_config = yaml.safe_load(f)

billingAgent_config = agents_config["billing_agent"]
prompt_location = "./config/" + billingAgent_config["system_prompt"]
with open(prompt_location, "r") as f:
    SYSTEM_PROMPT = f.read()


def billingAgent(state: AgentState, config: RunnableConfig) -> AgentState:
    tasks = state["tasks"]
    collection = config["configurable"]["collection"]
    retriever_tool = get_retriever_tool(collection)

    current_task = next(
        t for t in tasks
        if t["intent"] == "billing"
        and t["status"] == "pending"
    )

    model = ChatGoogleGenerativeAI(
        model=billingAgent_config["model"], temperature=billingAgent_config["temperature"])
    model_with_tool = model.bind_tools([retriever_tool])

    response = model_with_tool.invoke(
        [SystemMessage(content=SYSTEM_PROMPT),
         *state["messages"], SystemMessage(content=f"Your task:\n\n task: {current_task['task']}\n\nsummary: {current_task['summary']}\n\nentities: {', '.join(current_task['entities'])}")]
    )
    if response.tool_calls:
        return {
            "messages": [response]
        }

    current_task["status"] = "completed"
    return {
        "tasks": tasks,
        "agent_outputs": state["agent_outputs"] + [AgentOutput(agent="billing", task=current_task["task"], response=response.content)]
    }
