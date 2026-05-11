import logging
import yaml

from langchain_google_genai import ChatGoogleGenerativeAI
from config.schema import AgentState
from langchain_core.messages import SystemMessage
from retrieval.retriever import get_retriever_tool
from config.schema import AgentOutput
from langchain_core.runnables import RunnableConfig

logger = logging.getLogger(__name__)

with open("./config/agents.yaml", "r") as f:
    agents_config = yaml.safe_load(f)

technicalAgent_config = agents_config["technical_agent"]
prompt_location = "./config/" + technicalAgent_config["system_prompt"]
with open(prompt_location, "r") as f:
    SYSTEM_PROMPT = f.read()


def technicalAgent(state: AgentState, config: RunnableConfig) -> AgentState:
    """
    Technical agent responsible for handling technical tasks. It uses a language model
    to process the task and may call tools if needed. If the agent fails, it marks the task
    as failed and provides a fallback response for escalation.
    """
    tasks = state["tasks"]
    collection = config["configurable"]["collection"]
    retriever_tool = get_retriever_tool(collection)

    current_task = next(
        t for t in tasks
        if t["intent"] == "technical"
        and t["status"] == "pending"
    )

    try:
        model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
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
        content = response.content
        if isinstance(content, list):
            content = "".join([block.get("text", "")
                              for block in content if isinstance(block, dict)])
        return {
            "tasks": tasks,
            "agent_outputs": state["agent_outputs"] + [AgentOutput(agent="technical", task=current_task["task"], task_status="completed", response=content)]
        }
    except Exception:
        logger.exception("Technical agent failed")
        current_task["status"] = "failed"
        fallback = "Technical agent failed. Please escalate this query to a human operator.\n Task details:\n" + \
            current_task["task"] + "\nSummary:\n" + current_task["summary"] + \
            "\nEntities:\n" + ", ".join(current_task["entities"])
        return {
            "tasks": tasks,
            "agent_outputs": state["agent_outputs"] + [AgentOutput(agent="technical", task=current_task["task"], task_status="failed", response=fallback)]
        }
