import logging
import yaml

from config.schema import AgentState
from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)

with open("./config/agents.yaml", "r") as f:
    agents_config = yaml.safe_load(f)

finalizerAgent_config = agents_config["finalizer_agent"]
prompt_location = "./config/" + finalizerAgent_config["system_prompt"]
with open(prompt_location, "r") as f:
    SYSTEM_PROMPT = f.read()


def finalizer(state: AgentState) -> AgentState:
    """
    Agent responsible for finalizing the response after all tasks have been processed by the respective agents.
    It takes the outputs from all agents, compiles them, and generates a final response to be sent back to the user. 
    This agent ensures that the final output is coherent and addresses all aspects of the user's query based on the individual agent responses.
    """
    outputs = state["agent_outputs"]
    try:
        model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
        final_response = model.invoke(
            [SystemMessage(content=SYSTEM_PROMPT),
             *state["messages"],
             *[SystemMessage(content=f"Agent: {output['agent'].capitalize()}\n Agent Task: {output['task']}\n Task Status: {output['task_status']}\n Agent Response: {output['response']}") for output in outputs]]
        )
        return {"messages": [final_response]}
    except Exception:
        logger.exception("Finalizer failed")
        fallback = "We are sorry, but we were unable to process your request at this time. Please try again later or contact support for assistance."
        return {"messages": [SystemMessage(content=fallback)]}
