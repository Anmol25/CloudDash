import logging
import yaml

from langchain_google_genai import ChatGoogleGenerativeAI
from config.schema import AgentState
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from retrieval.retriever import knowledge_base_retriever
from config.schema import AgentOutput

logger = logging.getLogger(__name__)

with open("./config/agents.yaml", "r") as f:
    agents_config = yaml.safe_load(f)

billingAgent_config = agents_config["billing_agent"]
prompt_location = "./config/" + billingAgent_config["system_prompt"]
with open(prompt_location, "r") as f:
    SYSTEM_PROMPT = f.read()


def billingAgent(state: AgentState, config: RunnableConfig) -> AgentState:
    """
    Agent responsible for handling billing-related tasks. It processes the assigned task using a language model and may utilize tools if necessary. 
    In case of failure, it marks the task as failed and provides a fallback response for escalation to a human operator.
    """
    tasks = state["tasks"]

    current_task = next(
        t for t in tasks
        if t["intent"] == "billing"
        and t["status"] == "pending"
    )

    try:
        model = ChatGoogleGenerativeAI(
            model=billingAgent_config["model"], temperature=billingAgent_config["temperature"])
        model_with_tool = model.bind_tools([knowledge_base_retriever])

        response = model_with_tool.invoke(
            [SystemMessage(content=SYSTEM_PROMPT),
             *state["messages"], SystemMessage(content=f"Your task:\n\n task: {current_task['task']}\n\nsummary: {current_task['summary']}\n\nentities: {', '.join(current_task['entities'])}")]
        )
        if response.tool_calls:
            return {
                "messages": [response]
            }

        current_task["status"] = "completed"
        content = response.content
        if isinstance(content, list):
            content = "".join([block.get("text", "")
                              for block in content if isinstance(block, dict)])
        return {
            "tasks": tasks,
            "agent_outputs": state["agent_outputs"] + [AgentOutput(agent="billing", task=current_task["task"], task_status="completed", response=content)]
        }
    except Exception:
        logger.exception("Billing agent failed")
        current_task["status"] = "failed"
        fallback = "Billing agent failed. Please escalate this query to a human operator.\n Task details:\n" + \
            current_task["task"] + "\nSummary:\n" + current_task["summary"] + \
            "\nEntities:\n" + ", ".join(current_task["entities"])
        return {
            "tasks": tasks,
            "agent_outputs": state["agent_outputs"] + [AgentOutput(agent="billing", task=current_task["task"], task_status="failed", response=fallback)]
        }
