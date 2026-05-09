from fastapi import APIRouter
from agents.orchestrator import AgentOrchestrator
from pydantic import BaseModel
from typing import Optional
import uuid
from langgraph.checkpoint.memory import MemorySaver
from retrieval.chroma_collections import get_collection

router = APIRouter()

checkpointer = MemorySaver()
collection = get_collection()


class AgentRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


@router.post('/agent')
def call_agent(request: AgentRequest):
    if not request.thread_id:
        thread_id = str(uuid.uuid4())
    else:
        thread_id = request.thread_id
    agent = AgentOrchestrator(collection=collection,
                              thread_id=thread_id, checkpointer=checkpointer)
    final_state = agent.run(request.message)
    return {"thread_id": thread_id, "final_state": final_state}
