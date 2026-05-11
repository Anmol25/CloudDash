import logging
from fastapi import APIRouter, HTTPException
from agents.orchestrator import AgentOrchestrator
from pydantic import BaseModel
from typing import Optional
import uuid
from langgraph.checkpoint.memory import MemorySaver
from retrieval.chroma_collections import get_collection
from fastapi.responses import StreamingResponse

router = APIRouter()

checkpointer = MemorySaver()
collection = get_collection()


class AgentRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


@router.post('/agent')
def call_agent(request: AgentRequest):
    """
    Endpoint to call the agent with a message and optional thread ID.
     - message: The input message for the agent.
     - thread_id: Optional thread ID to maintain conversation context. If not provided, a new thread ID will be generated.
    """
    logger = logging.getLogger(__name__)
    try:
        if not request.thread_id:
            thread_id = str(uuid.uuid4())
        else:
            thread_id = request.thread_id
        agent = AgentOrchestrator(collection=collection,
                                  thread_id=thread_id, checkpointer=checkpointer)
        return StreamingResponse(agent.run(request.message), media_type="application/x-ndjson")
    except Exception:
        logger.exception("Agent API request failed")
        raise HTTPException(status_code=500, detail="Agent request failed")
