from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from orchestrator import AgentState, Tasks
from langchain_core.messages import SystemMessage


class TriageAgentResponse(BaseModel):
    """Response from the triage agent containing a list of tasks with their intent, task description, priority, and associated entities."""
    tasks: list[Tasks]


def triageAgent(state: AgentState) -> AgentState:
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    structured_response = model.with_structured_output(TriageAgentResponse)
    response = structured_response.invoke(
        [SystemMessage(content="You are a helpful assistant that triages customer support requests into tasks with intent, task description and associated entities. Here there can be two types of intents: technical and billing. For technical issues, the task description should be a concise description of the technical problem to be solved. For billing issues, the task description should be a concise description of the billing issue to be resolved. The entities should include any relevant information extracted from the customer's message that can help in resolving the issue. In single query there can be multiple tasks with different intents. return all the tasks in the response."),
         *state["messages"]]
    )
    return {"tasks": response.tasks}
